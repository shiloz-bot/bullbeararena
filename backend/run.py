#!/usr/bin/env python3
"""BullBearArena backend runner."""
import sys
import os

# Add backend dir to path BEFORE anything else
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Also patch subprocess environment
os.environ["PYTHONPATH"] = backend_dir

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "bullbeararena.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload to avoid subprocess import issues
    )
