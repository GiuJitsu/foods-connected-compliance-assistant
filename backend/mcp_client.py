"""MCP client abstraction the agent loop depends on.

`MCPClient` is the interface agent_loop.py uses. Two implementations:
- `StdioMCPClient`: spawns mcp-server/server.py as a subprocess over stdio
  (mcp-integration-spec.md §2 "Transport") using the official `mcp` Python
  SDK's client primitives, and lets the model choose which of its tools to
  call (hard constraint #2 — this class never picks a tool, only executes
  what it's told).
- `FakeMCPClient`: an in-memory stand-in for tests — including one that
  refuses to connect at all, for the "MCP server unreachable" failure
  scenario (CLAUDE.md "Testing scenarios": "harness-level fault (fake MCP
  client refuses to connect); not data-dependent").
"""

from __future__ import annotations

import asyncio
import sys
from abc import ABC, abstractmethod
from contextlib import AsyncExitStack
from dataclasses import dataclass
from typing import Any, Optional


class MCPUnreachableError(Exception):
    """Raised when the MCP server subprocess cannot be reached/started.
    Mapped by agent_loop.py to status=FAILED, failure_reason=MCP_UNREACHABLE
    (specs/agent-spec.md §9 #1) — checked once at task start, the loop is
    never attempted if this fires (mcp-integration-spec.md §5)."""


@dataclass
class MCPToolResult:
    """Normalized shape of a completed tool call, independent of the raw MCP
    wire format."""

    content: dict  # the tool's own JSON result (success payload or its own {"error": ...} shape)


@dataclass
class MCPToolDef:
    name: str
    description: str
    input_schema: dict


class MCPClient(ABC):
    @abstractmethod
    async def connect(self) -> None:
        """Establish the connection. Must raise MCPUnreachableError (not let
        a transport exception leak) if the server can't be reached."""
        raise NotImplementedError

    @abstractmethod
    async def list_tools(self) -> list[MCPToolDef]:
        raise NotImplementedError

    @abstractmethod
    async def call_tool(self, name: str, arguments: dict) -> MCPToolResult:
        """Execute one tool call. No timeout handling here — the caller
        (agent_loop.py) wraps this in asyncio.wait_for using the per-call
        timeout bound (specs/agent-spec.md §3), since the timeout policy is
        an agent-loop concern, not an MCP-transport concern."""
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError


class StdioMCPClient(MCPClient):
    """Real client: spawns mcp-server/server.py as a subprocess per task
    (mcp-integration-spec.md §2) and speaks MCP over stdio."""

    def __init__(self, server_script: str, python_executable: Optional[str] = None):
        self._server_script = server_script
        self._python_executable = python_executable or sys.executable
        self._stack: Optional[AsyncExitStack] = None
        self._session = None

    async def connect(self) -> None:
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError as exc:  # mcp SDK not installed
            raise MCPUnreachableError(f"mcp SDK unavailable: {exc}") from exc

        params = StdioServerParameters(command=self._python_executable, args=[self._server_script])
        self._stack = AsyncExitStack()
        try:
            read, write = await self._stack.enter_async_context(stdio_client(params))
            session = await self._stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
        except Exception as exc:
            # Subprocess failed to start, handshake failed, etc. — this is
            # exactly the "MCP server unreachable" condition
            # (mcp-integration-spec.md §5/§9).
            await self._stack.aclose()
            self._stack = None
            raise MCPUnreachableError(str(exc)) from exc
        self._session = session

    async def list_tools(self) -> list[MCPToolDef]:
        if self._session is None:
            raise MCPUnreachableError("MCP session not connected")
        result = await self._session.list_tools()
        return [
            MCPToolDef(name=t.name, description=t.description or "", input_schema=t.inputSchema)
            for t in result.tools
        ]

    async def call_tool(self, name: str, arguments: dict) -> MCPToolResult:
        if self._session is None:
            raise MCPUnreachableError("MCP session not connected")
        result = await self._session.call_tool(name, arguments)
        # The MCP SDK wraps tool output as content blocks; FastMCP tools
        # returning a dict come back as a single text block containing JSON,
        # or as structuredContent depending on SDK version — handle both.
        if getattr(result, "structuredContent", None):
            return MCPToolResult(content=result.structuredContent)
        import json as _json

        for block in result.content:
            if getattr(block, "type", None) == "text":
                try:
                    return MCPToolResult(content=_json.loads(block.text))
                except _json.JSONDecodeError:
                    return MCPToolResult(content={"error": "SERVER_ERROR", "message": block.text})
        return MCPToolResult(content={"error": "SERVER_ERROR", "message": "empty tool result"})

    async def close(self) -> None:
        if self._stack is not None:
            await self._stack.aclose()
            self._stack = None
            self._session = None


class FakeMCPClient(MCPClient):
    """In-memory stand-in for tests. `tools` is the catalog list_tools()
    returns. `handler` maps tool name -> callable(arguments) -> dict (the raw
    tool result content, success or {"error": ...} shape) OR a callable that
    raises asyncio.TimeoutError / any Exception to simulate a mid-call fault.

    Set `refuses_to_connect=True` to simulate the "MCP server unreachable at
    task start" scenario without any data dependency.
    """

    def __init__(
        self,
        handlers: dict[str, Any],
        tools: Optional[list[MCPToolDef]] = None,
        refuses_to_connect: bool = False,
    ):
        self._handlers = handlers
        self._tools = tools or [MCPToolDef(name=n, description="", input_schema={}) for n in handlers]
        self._refuses_to_connect = refuses_to_connect
        self.calls: list[tuple[str, dict]] = []
        self.connected = False

    async def connect(self) -> None:
        if self._refuses_to_connect:
            raise MCPUnreachableError("fake MCP client configured to refuse connection")
        self.connected = True

    async def list_tools(self) -> list[MCPToolDef]:
        return self._tools

    async def call_tool(self, name: str, arguments: dict) -> MCPToolResult:
        self.calls.append((name, arguments))
        if name not in self._handlers:
            return MCPToolResult(content={"error": "SERVER_ERROR", "message": f"no fake handler for tool {name}"})
        result = self._handlers[name](arguments)
        # Handlers may be plain callables returning a dict, or async
        # callables (coroutine functions) that actually `await
        # asyncio.sleep(...)` — used to simulate the SUP-TIMEOUT-01 fixture's
        # real-time-delay behaviour so agent_loop's asyncio.wait_for
        # per-call-timeout wrapping genuinely fires in tests.
        if asyncio.iscoroutine(result):
            result = await result
        return MCPToolResult(content=result)

    async def close(self) -> None:
        self.connected = False
