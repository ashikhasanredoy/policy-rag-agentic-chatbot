#!/usr/bin/env python3
"""
Enterprise Policy RAG System - Unified Application Launcher
Runs both the FastAPI backend and React (Vite) frontend concurrently.
Provides auto-prerequisite validation, health probing, and clean shutdown.
"""

import os
import sys
import time
import socket
import signal
import shutil
import urllib.request
import argparse
import webbrowser
import subprocess
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
BACKEND_DIR = PROJECT_ROOT / "backend"
ENV_FILE = PROJECT_ROOT / ".env"
ENV_EXAMPLE = PROJECT_ROOT / ".env.example"
CHROMA_DIR = PROJECT_ROOT / "vectorstore" / "chroma_db"
PARENT_SECTIONS_FILE = PROJECT_ROOT / "processed" / "parent_sections.json"

# Default configuration
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000
FRONTEND_PORT = 5173

# Ensure common paths (brew, node, pyenv) are in PATH
_extra_paths = [
    Path.home() / ".pyenv/shims",
    Path("/usr/local/bin"),
    Path("/opt/homebrew/bin"),
    Path.home() / ".nvm/versions/node/current/bin",
]
for p in _extra_paths:
    p_str = str(p)
    if p.exists() and p_str not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{p_str}:{os.environ.get('PATH', '')}"

# Active process references for graceful termination
processes = []


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Checks whether a local TCP port is already bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.8)
        return s.connect_ex((host, port)) == 0


def ensure_environment_file():
    """Ensures .env exists; copies from .env.example if absent."""
    if not ENV_FILE.exists() and ENV_EXAMPLE.exists():
        print("📄 Initializing .env configuration from .env.example...")
        shutil.copy2(ENV_EXAMPLE, ENV_FILE)


def check_prerequisites(skip_frontend: bool = False):
    """Verifies core Python dependencies, Node.js, and index assets."""
    print("🔍 Checking prerequisites...")

    # 1. Python core package validation
    required_packages = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("langgraph", "langgraph"),
        ("chromadb", "chromadb"),
        ("rank_bm25", "rank-bm25"),
        ("sqlalchemy", "sqlalchemy"),
        ("pydantic", "pydantic"),
    ]

    missing = []
    for import_name, pkg_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pkg_name)

    if missing:
        print(f"\n❌ Missing required Python package(s): {', '.join(missing)}")
        print("👉 Please install dependencies: pip install -r requirements.txt\n")
        sys.exit(1)

    # 2. Node.js & npm validation
    if not skip_frontend:
        npm_path = shutil.which("npm")
        if not npm_path:
            print("\n❌ 'npm' executable not found in PATH.")
            print("👉 Please install Node.js (v18+) from https://nodejs.org/\n")
            sys.exit(1)

        # Ensure frontend dependencies are installed
        node_modules = FRONTEND_DIR / "node_modules"
        if not node_modules.exists():
            print("📦 Installing frontend dependencies (npm install in frontend/)...")
            res = subprocess.run([npm_path, "install"], cwd=FRONTEND_DIR)
            if res.returncode != 0:
                print("❌ 'npm install' failed. Please resolve npm dependencies and try again.")
                sys.exit(1)

    # 3. Knowledge base & index readiness check
    if not CHROMA_DIR.exists() or not PARENT_SECTIONS_FILE.exists():
        print("🏛️  Pre-indexing 150 enterprise policy documents into ChromaDB...")
        ingest_script = PROJECT_ROOT / "scripts" / "ingest_markdown_policies.py"
        if ingest_script.exists():
            res = subprocess.run([sys.executable, str(ingest_script)], cwd=PROJECT_ROOT)
            if res.returncode != 0:
                print("⚠️  Initial ingestion finished with non-zero exit code. Continuing...")

    print("✅ All prerequisites and dependencies verified.\n")


def wait_for_backend(host: str, port: int, timeout: float = 20.0) -> bool:
    """Polls the backend health endpoint until it returns HTTP 200."""
    url = f"http://{host}:{port}/api/v1/health/"
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "RunLauncher/1.0"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def wait_for_port(port: int, host: str = "127.0.0.1", timeout: float = 15.0) -> bool:
    """Polls until a local TCP port is bound and accepting connections."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_in_use(port, host):
            return True
        time.sleep(0.3)
    return False


def shutdown_processes(signum=None, frame=None):
    """Gracefully terminates all spawned background processes."""
    print("\n🛑 Shutting down Enterprise Policy RAG services...")
    for p in processes:
        if p.poll() is None:
            try:
                if sys.platform != "win32":
                    os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                else:
                    p.terminate()
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass

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
        "--frontend-port",
        type=int,
        default=FRONTEND_PORT,
        help=f"Frontend port (default: {FRONTEND_PORT})",
    )
    parser.add_argument(
        "--open-browser",
        "--browser",
        dest="open_browser",
        action="store_true",
        default=False,
        help="Open the frontend in your default browser once ready",
    )
    parser.add_argument(
        "--no-browser",
        dest="open_browser",
        action="store_false",
        help="Do not open the browser automatically",
    )
    args = parser.parse_args()

    # Register exit signal handlers
    signal.signal(signal.SIGINT, shutdown_processes)
    signal.signal(signal.SIGTERM, shutdown_processes)

    print("=" * 70)
    print("🛡️  Enterprise Policy Hybrid RAG Retrieval System (150 Policies)")
    print("=" * 70)

    ensure_environment_file()
    check_prerequisites(skip_frontend=args.no_frontend)

    # 1. Start Backend Server
    if not args.no_backend:
        if is_port_in_use(args.backend_port, args.host):
            # Check if an existing backend instance is already healthy
            if wait_for_backend(args.host, args.backend_port, timeout=1.0):
                print(f"ℹ️  Backend already running and healthy on http://{args.host}:{args.backend_port}")
            else:
                print(f"⚠️  Port {args.backend_port} is in use by another process.")
        else:
            print(f"🚀 Starting FastAPI backend on http://{args.host}:{args.backend_port}...")
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
            backend_proc = subprocess.Popen(
                backend_cmd,
                cwd=PROJECT_ROOT,
                preexec_fn=os.setsid if sys.platform != "win32" else None,
            )
            processes.append(backend_proc)

            # Health-check probe
            print("⏳ Waiting for backend API to be ready...")
            if wait_for_backend(args.host, args.backend_port, timeout=20.0):
                print(f"✅ Backend API is healthy and accepting requests.")
            else:
                print(f"⚠️  Backend startup taking longer than expected. Continuing...")

    # 2. Start Frontend Server
    if not args.no_frontend:
        npm_bin = shutil.which("npm") or "npm"
        if is_port_in_use(args.frontend_port):
            print(f"ℹ️  Port {args.frontend_port} is busy. Vite will select the next available port.")

        print(f"🎨 Starting React frontend dev server (Vite)...")
        frontend_cmd = [npm_bin, "run", "dev"]
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=FRONTEND_DIR,
            preexec_fn=os.setsid if sys.platform != "win32" else None,
        )
        processes.append(frontend_proc)

        # Wait for frontend port
        wait_for_port(args.frontend_port, timeout=10.0)

    # 3. Display Connection Summary
    print("\n" + "=" * 70)
    print("✨ Enterprise Policy RAG Services are Running!")
    print("=" * 70)
    if not args.no_frontend:
        print(f"   🌐 Web Chat Interface: http://localhost:{args.frontend_port}")
    if not args.no_backend:
        print(f"   ⚙️  Backend REST API:   http://{args.host}:{args.backend_port}")
        print(f"   📚 Interactive Docs:   http://{args.host}:{args.backend_port}/docs")
    print("=" * 70)
    print("Press [Ctrl+C] to stop all services.\n")

    # 4. Open Browser if requested
    if args.open_browser and not args.no_frontend:
        webbrowser.open(f"http://localhost:{args.frontend_port}")

    # 5. Monitor Process Health
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
