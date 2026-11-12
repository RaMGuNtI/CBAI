import sys
import os
import subprocess
import argparse
import time
import signal
from pathlib import Path


def get_python_executable():
    venv_python = Path(__file__).parent / "venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def start_backend(python_exe: str):
    print("🚀 Starting CustomBot AI FastAPI Backend on http://127.0.0.1:8000 ...")
    cmd = [python_exe, "-m", "uvicorn", "app.backend.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.resolve())
    return subprocess.Popen(cmd, env=env)


def start_frontend(python_exe: str):
    print("🎨 Starting CustomBot AI Streamlit Frontend on http://127.0.0.1:8501 ...")
    streamlit_app = str(Path(__file__).parent / "app" / "frontend" / "streamlit_app.py")
    cmd = [python_exe, "-m", "streamlit", "run", streamlit_app, "--server.port", "8501", "--server.headless", "true"]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.resolve())
    return subprocess.Popen(cmd, env=env)


def run_tests(python_exe: str):
    print("🧪 Executing CustomBot AI Test Suite via pytest...")
    cmd = [python_exe, "-m", "pytest", "-v"]
    env = os.environ.copy()
    env["TESTING"] = "1"
    return subprocess.run(cmd, env=env).returncode


def main():
    parser = argparse.ArgumentParser(description="CustomBot AI — No-Code RAG Chatbot Builder Launcher")
    parser.add_argument("--backend", action="store_true", help="Launch FastAPI backend only")
    parser.add_argument("--frontend", action="store_true", help="Launch Streamlit frontend only")
    parser.add_argument("--test", action="store_true", help="Execute the test suite and exit")
    args = parser.parse_args()

    python_exe = get_python_executable()

    if args.test:
        sys.exit(run_tests(python_exe))

    procs = []

    try:
        if args.backend:
            p_back = start_backend(python_exe)
            procs.append(p_back)
            p_back.wait()
        elif args.frontend:
            p_front = start_frontend(python_exe)
            procs.append(p_front)
            p_front.wait()
        else:
            p_back = start_backend(python_exe)
            procs.append(p_back)
            time.sleep(2)
            p_front = start_frontend(python_exe)
            procs.append(p_front)

            print("\n" + "=" * 65)
            print("🤖 CustomBot AI Platform is running!")
            print("   👉 Streamlit Dashboard:  http://127.0.0.1:8501")
            print("   👉 FastAPI Swagger Docs: http://127.0.0.1:8000/docs")
            print("   👉 Health Check:        http://127.0.0.1:8000/health")
            print("=" * 65 + "\n")
            print("Press Ctrl+C to terminate all services.\n")

            while True:
                time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Shutting down CustomBot AI services...")
        for p in procs:
            p.terminate()
            try:
                p.wait(timeout=3)
            except Exception:
                p.kill()
        print("Done. Goodbye!")


if __name__ == "__main__":
    main()

