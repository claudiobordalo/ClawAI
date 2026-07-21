"""
ClawAI Backend Server - Entry point for Electron integration.

This module starts the FastAPI server with WebSocket support
for the ClawAI Electron desktop application.
"""

import argparse
import sys
import os
from pathlib import Path

# Ensure clawai package is importable
sys.path.insert(0, str(Path(__file__).parent))

from clawai.api.application import create_app


def main():
    parser = argparse.ArgumentParser(description="ClawAI Backend Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers")
    parser.add_argument("--reload", action="store_true", default=False, help="Enable auto-reload")
    args = parser.parse_args()

    # Create and configure the app
    app = create_app()

    # Write port to file for Electron to discover
    user_data = os.environ.get("CLAWAI_USER_DATA", "")
    if user_data:
        port_file = os.path.join(user_data, "backend_port.txt")
        try:
            with open(port_file, "w") as f:
                f.write(str(args.port))
        except Exception as e:
            print(f"[server] Warning: Could not write port file: {e}", file=sys.stderr)

    print(f"[server] Starting on {args.host}:{args.port}", flush=True)

    # Start uvicorn
    import uvicorn
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        workers=args.workers,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
