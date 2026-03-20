"""
Start the Physics Engine Log API server.
Usage:
    python run_server.py
Env vars:
    PHYSICS_HOST  (default: 127.0.0.1)
    PHYSICS_PORT  (default: 8010)
"""
import os
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent / 'src'))

import uvicorn
from physics_engine.log_api import create_log_app

HOST = os.getenv("PHYSICS_HOST", "127.0.0.1")
PORT = int(os.getenv("PHYSICS_PORT", "8010"))

if __name__ == "__main__":
    print("  Physics Engine Log API")
    print(f"  Listening : http://{HOST}:{PORT}")
    print(f"  Docs      : http://{HOST}:{PORT}/docs")
    print(f"  Log files : http://{HOST}:{PORT}/logs")
    print()
    uvicorn.run(create_log_app(), host=HOST, port=PORT, log_level="info")
