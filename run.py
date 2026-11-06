#!/usr/bin/env python3
"""
Enterprise Policy RAG System - Unified Launcher
Runs both the FastAPI backend and React (Vite) frontend concurrently.
"""

import os
import sys
import time
import socket
import signal
import shutil
import argparse
import webbrowser
import subprocess
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
BACKEND_DIR = PROJECT_ROOT / "backend"

# Default configuration
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000
FRONTEND_PORT = 5173

# Ensure common paths (brew, node, pyenv) are in PATH
_extra_paths = [
    Path.home() / ".pyenv/shims",
    Path("/usr/local/bin"),
    Path("/opt/homebrew/bin"),
]
for p in _extra_paths:
    p_str = str(p)
    if p.exists() and p_str not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{p_str}:{os.environ.get('PATH', '')}"

# Process references for clean shutdown
processes = []


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a local port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex((host, port)) == 0


def check_prerequisites(skip_frontend: bool = False):
    """Verify required tools and dependencies are installed."""
    print("🔍 Checking prerequisites...")

    # Python dependencies check
    try:
        import fastapi
        import uvicorn
        import langgraph
        import qdrant_client
    except ImportError as e:
        print(f"\n❌ Missing required Python package: {e.name}")
        print(f"👉 Please install dependencies: pip install -r backend/requirements.txt\n")
        sys.exit(1)

    # Node / npm check
    if not skip_frontend:
        npm_path = shutil.which("npm")
        if not npm_path:
            print("\n❌ 'npm' executable not found in PATH.")
            print("👉 Please install Node.js (v18+) from https://nodejs.org/\n")
            sys.exit(1)

        # Check frontend node_modules
        node_modules = FRONTEND_DIR / "node_modules"
        if not node_modules.exists():
            print("📦 Installing frontend dependencies (npm install)...")
            res = subprocess.run([npm_path, "install"], cwd=FRONTEND_DIR)
            if res.returncode != 0:
                print("❌ 'npm install' failed. Please resolve npm dependencies and try again.")
                sys.exit(1)

    print("✅ Prerequisites verified successfully.\n")


def shutdown_processes(signum=None, frame=None):
    """Gracefully terminate all spawned background processes."""
    print("\n🛑 Shutting down Enterprise Policy RAG services...")
    for p in processes:
        if p.poll() is None:
            try:
                # Terminate the process group to kill child processes (e.g. node spawned by npm)
                if sys.platform != "win32":
                    os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                else:
                    p.terminate()
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass

    # Wait for processes to exit
    for p in processes:
        try:
            p.wait(timeout=3)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass

    print("👋 All services stopped cleanly. Goodbye!\n")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="Run Enterprise Policy RAG System (Backend + Frontend)"
    )
    parser.add_argument(
        "--no-frontend",
        action="store_true",
        help="Run backend server only",
    )
    parser.add_argument(
        "--no-backend",
        action="store_true",
        help="Run frontend server only",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=BACKEND_HOST,
        help=f"Backend host (default: {BACKEND_HOST})",
    )
    parser.add_argument(
        "--backend-port",
        type=int,
        default=BACKEND_PORT,
        help=f"Backend port (default: {BACKEND_PORT})",
    )
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open the frontend in your default browser once ready",
    )
    args = parser.parse_args()

    # Register exit signal handlers
    signal.signal(signal.SIGINT, shutdown_processes)
    signal.signal(signal.SIGTERM, shutdown_processes)

    print("=" * 65)
    print("🛡️  Enterprise Policy RAG + Agentic AI Assistant")
    print("=" * 65)

    check_prerequisites(skip_frontend=args.no_frontend)

    # Port availability check
    if not args.no_backend and is_port_in_use(args.backend_port, args.host):
        print(f"⚠️  Warning: Port {args.backend_port} is already in use.")
        print(f"👉 Ensure no other instance is running, or specify --backend-port <port>.\n")

    if not args.no_frontend and is_port_in_use(FRONTEND_PORT):
        print(f"ℹ️  Note: Port {FRONTEND_PORT} is in use. Vite will automatically choose the next free port.\n")

    # Start Backend
    if not args.no_backend:
        print(f"🚀 Starting Backend server on http://{args.host}:{args.backend_port}...")
        backend_cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.app.main:app",
            "--host",
            args.host,
            "--port",
            str(args.backend_port),
            "--reload",
        ]
        
        # Start in new process group for clean termination
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=PROJECT_ROOT,
            preexec_fn=os.setsid if sys.platform != "win32" else None,
        )
        processes.append(backend_proc)

    # Start Frontend
    if not args.no_frontend:
        npm_bin = shutil.which("npm") or "npm"
        print(f"🎨 Starting Frontend UI (Vite dev server)...")
        frontend_cmd = [npm_bin, "run", "dev"]
        
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=FRONTEND_DIR,
            preexec_fn=os.setsid if sys.platform != "win32" else None,
        )
        processes.append(frontend_proc)

    # Brief delay for servers to bind
    time.sleep(2)

    print("\n" + "=" * 65)
    print("✨ Services are running!")
    if not args.no_frontend:
        print(f"   🌐 Frontend UI:        http://localhost:{FRONTEND_PORT}")
    if not args.no_backend:
        print(f"   ⚙️  Backend API:        http://{args.host}:{args.backend_port}")
        print(f"   📚 Swagger Docs:       http://{args.host}:{args.backend_port}/docs")
    print("=" * 65)
    print("Press [Ctrl+C] to stop all services.\n")

    if args.open_browser and not args.no_frontend:
        webbrowser.open(f"http://localhost:{FRONTEND_PORT}")

    # Keep script alive and monitor process health
    try:
        while True:
            time.sleep(1)
            for p in processes:
                exit_code = p.poll()
                if exit_code is not None:
                    print(f"\n⚠️  A service process exited unexpectedly with code {exit_code}.")
                    shutdown_processes()
    except KeyboardInterrupt:
        shutdown_processes()


if __name__ == "__main__":
    main()

