"""Ensures mcp-server/ itself is on sys.path, so test modules can
`import server` directly — matching how server.py is run/imported elsewhere
(flat module, no package prefix)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
