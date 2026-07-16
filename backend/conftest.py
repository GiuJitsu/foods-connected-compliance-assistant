"""Ensures backend/ itself (not just backend/tests/) is on sys.path, so test
modules can `from agent_loop import run_task` etc. without a package prefix —
matching how main.py/agent_loop.py import each other (flat, run from
backend/ as the working directory, e.g. `uvicorn main:app`)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
