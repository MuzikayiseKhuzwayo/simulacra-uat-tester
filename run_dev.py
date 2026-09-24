"""Simulacra UAT - Full Stack Development Runner.

Launches both:
1. FastAPI Backend Engine (port 8000)
2. Next.js 15 Web Application (port 3000)
"""

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT / "frontend"


def main():
    print("=" * 60)
    print("🚀 Starting Simulacra UAT Platform (FastAPI + Next.js)")
    print("=" * 60)

    # 1. Start FastAPI backend
    print("📡 [1/2] Launching FastAPI Backend on http://127.0.0.1:8000 ...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.api.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
        cwd=str(ROOT),
    )

    # Wait 2 seconds for backend to initialize
    time.sleep(2)

    # 2. Start Next.js frontend
    print("💻 [2/2] Launching Next.js 15 Frontend on http://localhost:3000 ...")
    frontend_proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(FRONTEND_DIR),
        shell=True,
    )

    print("\n" + "=" * 60)
    print("🎉 Simulacra UAT Platform is Live!")
    print("👉 Frontend: http://localhost:3000")
    print("👉 Backend API Docs: http://127.0.0.1:8000/docs")
    print("=" * 60 + "\n")

    try:
        backend_proc.wait()
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Simulacra servers...")
        backend_proc.terminate()
        frontend_proc.terminate()


if __name__ == "__main__":
    main()
