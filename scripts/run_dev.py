"""Launch the existing backend/frontend together; preserve occupied ports.

Use the project's virtual-environment Python. Ctrl+C stops this script's own
SUMO session and child servers. --smoke-test checks startup and exits.
"""
import argparse
import importlib.util
import json
import shutil
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def preflight():
    """Fail before launching children; optional research inputs stay optional."""
    required = ('fastapi', 'uvicorn', 'pydantic', 'pydantic_settings', 'httpx', 'numpy', 'traci', 'sumolib', 'websockets')
    missing = [name for name in required if importlib.util.find_spec(name) is None]
    if missing:
        raise RuntimeError('Missing backend dependencies: '+', '.join(missing)+'. Install: '+sys.executable+' -m pip install -r backend/requirements.txt')
    executable = shutil.which('sumo')
    if not executable:
        raise RuntimeError('SUMO executable missing from PATH. Install SUMO and add its bin directory to PATH.')
    version = subprocess.run([executable, '--version'], capture_output=True, text=True, timeout=10, check=True).stdout.splitlines()[0]
    if not shutil.which('node') or not shutil.which('npm.cmd' if os.name == 'nt' else 'npm'):
        raise RuntimeError('Node.js/npm missing from PATH. Install Node.js before launching the frontend.')
    if not (ROOT/'node_modules/vite/package.json').is_file() or not (ROOT/'node_modules/react/package.json').is_file():
        raise RuntimeError('Frontend dependencies missing. Run npm.cmd ci from the project folder.')
    print('Backend dependencies: available | Python '+sys.version.split()[0], flush=True)
    print('SUMO verified: '+version+' | '+executable, flush=True)
    print('Frontend dependencies: available | '+subprocess.check_output([shutil.which('node'), '--version'], text=True).strip(), flush=True)
    print('Optional inputs: camera packages '+('available' if all(importlib.util.find_spec(m) for m in ('cv2', 'ultralytics')) else 'unavailable')+
          '; torch '+('available' if importlib.util.find_spec('torch') else 'unavailable')+'. Learned policy requires qualification.', flush=True)


def read_json(url):
    with urlopen(url, timeout=2) as response:
        return json.load(response)


def run(backend_port=8001, frontend_port=3001, smoke_test=False):
    if backend_port == frontend_port or not all(1 <= p <= 65535 for p in (backend_port, frontend_port)):
        raise ValueError("Choose distinct backend/frontend ports from 1 to 65535")
    preflight()
    for port in (backend_port, frontend_port):
        with socket.socket() as check:
            try:
                check.bind(("127.0.0.1", port))
            except OSError as exc:
                raise RuntimeError(f"Port {port} is occupied. Existing service preserved; choose another --backend-port/--frontend-port.") from exc
    environment = os.environ.copy()
    environment.update(DEBUG="false", VITE_BACKEND_API_URL=f"http://127.0.0.1:{backend_port}/api/v1")
    camera_config = environment.get('SYNCHROFLOW_CAMERA_CONFIG')
    if camera_config:
        camera_path = Path(camera_config).expanduser().resolve()
        environment['SYNCHROFLOW_CAMERA_CONFIG'] = str(camera_path)
        print('Camera config: '+str(camera_path)+(' (found)' if camera_path.is_file() else ' (missing; camera start will fail, SUMO remains available)'), flush=True)
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    commands = [([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(backend_port)], ROOT / "backend"),
                (([os.environ.get("COMSPEC", "cmd.exe"), "/c", "npm.cmd"] if os.name == "nt" else ["npm"]) + ["run", "dev", "--", "--host", "127.0.0.1", "--port", str(frontend_port)], ROOT)]
    children = []
    backend_ready = False
    try:
        for command, cwd in commands:
            children.append(subprocess.Popen(command, cwd=cwd, env=environment, creationflags=flags))
        urls = [f"http://127.0.0.1:{backend_port}/api/v1/health", f"http://127.0.0.1:{frontend_port}"]
        deadline = time.monotonic() + 40
        for index, url in enumerate(urls):
            while True:
                if any(child.poll() is not None for child in children):
                    raise RuntimeError("A development server exited; inspect its output")
                try:
                    with urlopen(url, timeout=1) as response:
                        content = response.read().decode('utf-8')
                        valid = json.loads(content).get('status') == 'ok' if index == 0 else '<div id="root">' in content
                        if response.status == 200 and valid:
                            if index == 0:
                                backend_ready = True
                            print(('Backend ready: ' if index == 0 else 'Frontend ready: ')+url, flush=True)
                            break
                except (OSError, ValueError):
                    pass
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"Server startup timed out: {url}")
                time.sleep(0.2)
        state = read_json(f'http://127.0.0.1:{backend_port}/api/v1/sumo/status')
        simulation = 'running' if state['running'] else ('paused' if state['connected'] else 'stopped')
        print(f"Controller: {state['controller']} | scenario: {state['scenario']} | simulation: {simulation} | MAPPO enabled: {state['mappoStatus']['operationalPolicyEnabled']}", flush=True)
        print(f"Prototype ready: {urls[1]} | backend: {urls[0]}", flush=True)
        if not smoke_test:
            while all(child.poll() is None for child in children):
                time.sleep(0.5)
            raise RuntimeError("A server exited unexpectedly; both owned servers will be stopped")
    except KeyboardInterrupt:
        pass
    finally:
        if backend_ready and children and children[0].poll() is None:
            for action in ('sumo/stop', 'perception/stop'):
                try:
                    with urlopen(Request(f"http://127.0.0.1:{backend_port}/api/v1/{action}", method="POST"), timeout=8):
                        pass
                except OSError:
                    pass
        for child in reversed(children):
            if child.poll() is None:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(child.pid), "/T", "/F"], capture_output=True, check=False)
                else:
                    child.terminate()
                child.wait(timeout=10)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend-port", type=int, default=8001)
    parser.add_argument("--frontend-port", type=int, default=3001)
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    try:
        run(args.backend_port, args.frontend_port, args.smoke_test)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print('Startup failed: '+str(exc), file=sys.stderr)
        raise SystemExit(1)
