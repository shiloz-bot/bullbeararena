"""Simple runner script for BullBearArena backend."""

import sys
import os

# Ensure the backend directory is in sys.path AND PYTHONPATH (for uvicorn reload subprocess)
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Set PYTHONPATH so uvicorn's reload subprocess can also find the package
os.environ["PYTHONPATH"] = backend_dir

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "bullbeararena.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[backend_dir],
    )
