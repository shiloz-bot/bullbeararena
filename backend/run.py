#!/usr/bin/env python3
"""BullBearArena backend runner."""
import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Load .env file
from dotenv import load_dotenv
load_dotenv(os.path.join(backend_dir, ".env"))

from bullbeararena.api.app import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
