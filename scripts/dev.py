"""Development bootstrap and runner for the SWEN AIOps prototype.

Usage examples (from repo root):
  # one-shot setup: create venv, install deps, build frontend
  python scripts/dev.py --setup --install --build-frontend

  # start backend and simulator (background, logs in ./logs)
  python scripts/dev.py --start-backend --start-simulator --background

  # full quick start (create venv, install, build, start services)
  python scripts/dev.py --quickstart --background

This script is cross-platform and does not require you to "activate" the venv manually.
It creates a venv at ./.venv and invokes the venv python directly for installs and running.

It writes logs to ./logs/backend.log and ./logs/simulator.log when services are started.
"""
from __future__ import annotations
import argparse
import os
import subprocess
import sys
import venv
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV_DIR = ROOT / '.venv'
LOG_DIR = ROOT / 'logs'
API_REQ = ROOT / 'api' / 'requirements.txt'
FRONTEND_DIR = ROOT / 'frontend'
SIMULATOR_MODULE = 'ai_engine.simulator'


def venv_python() -> Path:
    if os.name == 'nt':
        return VENV_DIR / 'Scripts' / 'python.exe'
    return VENV_DIR / 'bin' / 'python'


def ensure_venv():
    if VENV_DIR.exists():
        print(f"Using existing venv at {VENV_DIR}")
        return
    print(f"Creating venv at {VENV_DIR}...")
    venv.create(VENV_DIR, with_pip=True)
    print("venv created")


def run_pip_install(requirements: Path):
    py = venv_python()
    if not py.exists():
        raise RuntimeError("venv python not found; run --setup first")
    if not requirements.exists():
        print(f"No requirements file at {requirements}; skipping pip install")
        return
    print(f"Installing Python requirements from {requirements}...")
    subprocess.check_call([str(py), '-m', 'pip', 'install', '--upgrade', 'pip'])
    subprocess.check_call([str(py), '-m', 'pip', 'install', '-r', str(requirements)])
    print("Python requirements installed")


def build_frontend():
    if not (FRONTEND_DIR.exists() and (FRONTEND_DIR / 'package.json').exists()):
        print('No frontend package.json found; skipping frontend build')
        return
    print('Building frontend (npm ci && npm run build)')
    npm = shutil.which('npm')
    if not npm:
        print('npm not found in PATH; please install Node.js and npm to build the frontend')
        return
    subprocess.check_call(['npm', 'ci'], cwd=str(FRONTEND_DIR))
    subprocess.check_call(['npm', 'run', 'build'], cwd=str(FRONTEND_DIR))
    print('Frontend built into frontend/dist')


def start_backend(background: bool = False):
    py = venv_python()
    if not py.exists():
        raise RuntimeError('venv python not found; run --setup first')
    # allow override via PORT env var for convenience
    port = os.environ.get('PORT', '8000')
    cmd = [str(py), '-m', 'uvicorn', 'api.main:app', '--host', '127.0.0.1', '--port', str(port)]
    print('Starting backend:', ' '.join(cmd))
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stdout = open(LOG_DIR / 'backend.log', 'ab')
    stderr = subprocess.STDOUT
    if background:
        proc = subprocess.Popen(cmd, cwd=str(ROOT), stdout=stdout, stderr=stderr)
        print(f'Backend started (PID {proc.pid}), logs: {LOG_DIR/"backend.log"}')
        return proc
    else:
        subprocess.check_call(cmd, cwd=str(ROOT))


def start_simulator(background: bool = False, interval: float = 5.0, backend_url: str = None):
    py = venv_python()
    if not py.exists():
        raise RuntimeError('venv python not found; run --setup first')
    # allow passing backend_url or derive from BACKEND_URL env or PORT env
    if backend_url:
        backend = backend_url
    else:
        backend = os.environ.get('BACKEND_URL')
        if not backend:
            port = os.environ.get('PORT', '8000')
            backend = f'http://127.0.0.1:{port}'
    cmd = [
        str(py), '-m', SIMULATOR_MODULE, '--mode', 'http',
        '--interval', str(interval), '--backend', backend,
    ]
    print('Starting simulator:', ' '.join(cmd))
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stdout = open(LOG_DIR / 'simulator.log', 'ab')
    stderr = subprocess.STDOUT
    if background:
        proc = subprocess.Popen(cmd, cwd=str(ROOT), stdout=stdout, stderr=stderr)
        print(f'Simulator started (PID {proc.pid}), logs: {LOG_DIR/"simulator.log"}')
        return proc
    else:
        subprocess.check_call(cmd, cwd=str(ROOT))


def run_quickstart(background: bool = True):
    ensure_venv()
    run_pip_install(API_REQ)
    build_frontend()
    # start backend and simulator in background
    backend_proc = start_backend(background=background)
    # give backend a sec
    time.sleep(1)
    sim_proc = start_simulator(background=background)
    return backend_proc, sim_proc


DEV_REQ = ROOT / 'dev-requirements.txt'


def run_install_dev():
    py = venv_python()
    if not py.exists():
        raise RuntimeError('venv python not found; run --setup first')
    if not DEV_REQ.exists():
        print(f'No dev requirements file at {DEV_REQ}; skipping')
        return
    print(f'Installing dev Python requirements from {DEV_REQ}...')
    subprocess.check_call([str(py), '-m', 'pip', 'install', '--upgrade', 'pip'])
    subprocess.check_call([str(py), '-m', 'pip', 'install', '-r', str(DEV_REQ)])
    print('Dev Python requirements installed')


def run_tests():
    py = venv_python()
    if not py.exists():
        raise RuntimeError('venv python not found; run --setup first')
    print('Running pytest...')
    subprocess.check_call([str(py), '-m', 'pytest', '-q'], cwd=str(ROOT))


def run_lint():
    py = venv_python()
    if not py.exists():
        raise RuntimeError('venv python not found; run --setup first')
    # Try ruff via PATH first
    ruff = shutil.which('ruff')
    if ruff:
        print('Running ruff...')
        subprocess.call(['ruff', 'check', str(ROOT)])
    else:
        # Try running ruff via python -m if installed in venv
        try:
            subprocess.check_call([str(py), '-m', 'ruff', 'check', str(ROOT)])
        except Exception:
            print('ruff not available; install it with --install-dev to run lint')
    # Try mypy on project packages only to avoid duplicate-module path warnings
    try:
        subprocess.check_call([str(py), '-m', 'mypy', 'api', 'ai_engine', 'scripts', 'tests'], cwd=str(ROOT))
    except Exception:
        print('mypy not available or found type issues; install with --install-dev to run type checks')


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--setup', action='store_true', help='Create venv')
    p.add_argument('--install', action='store_true', help='Install Python requirements into venv')
    p.add_argument('--build-frontend', action='store_true', help='Build frontend with npm')
    p.add_argument('--start-backend', action='store_true', help='Start backend (uvicorn)')
    p.add_argument('--start-simulator', action='store_true', help='Start simulator')
    p.add_argument('--backend-port', type=int, default=None, help='Port to use when starting backend')
    p.add_argument('--backend-url', type=str, default=None, help='Backend URL to pass to simulator')
    p.add_argument('--background', action='store_true', help='Start services in background (logs in ./logs)')
    p.add_argument('--quickstart', action='store_true', help='Run setup+install+build and start backend+simulator')
    p.add_argument('--sim-interval', type=float, default=5.0, help='Simulator interval in seconds')
    p.add_argument('--install-dev', action='store_true', help='Install development requirements into venv (pytest, ruff, mypy)')
    p.add_argument('--run-tests', action='store_true', help='Run pytest using the venv')
    p.add_argument('--lint', action='store_true', help='Run ruff and mypy if available')
    return p.parse_args()


def main():
    args = parse_args()
    try:
        if args.quickstart:
            run_quickstart(background=args.background)
            return
        if args.setup:
            ensure_venv()
        if args.install:
            ensure_venv()
            run_pip_install(API_REQ)
        if args.build_frontend:
            build_frontend()
        if args.start_backend:
            # allow CLI override of port
            if args.backend_port:
                os.environ['PORT'] = str(args.backend_port)
            start_backend(background=args.background)
        if args.start_simulator:
            start_simulator(
                background=args.background, interval=args.sim_interval, backend_url=args.backend_url
            )
        if args.install_dev:
            ensure_venv()
            run_install_dev()
        if args.run_tests:
            ensure_venv()
            run_tests()
        if args.lint:
            ensure_venv()
            run_lint()
    except subprocess.CalledProcessError as e:
        print('Command failed:', e)
        sys.exit(1)
    except Exception as e:
        print('Error:', e)
        sys.exit(2)

if __name__ == '__main__':
    main()
