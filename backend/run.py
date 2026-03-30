#!/usr/bin/env python3
"""Simple runner script for BullBearArena backend."""

import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))

# Set PYTHONPATH so uvicorn's reload subprocess can find the package
os.environ["PYTHONPATH"] = backend_dir
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "bullbeararena.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
