"""Startup failure paths must preserve services the launcher does not own."""
import importlib.util
from pathlib import Path
import socket
import pytest

spec = importlib.util.spec_from_file_location('synchroflow_run_dev', Path(__file__).resolve().parents[3]/'scripts/run_dev.py')
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


def test_missing_backend_dependencies_have_install_hint(monkeypatch):
    monkeypatch.setattr(launcher.importlib.util, 'find_spec', lambda name: None if name == 'fastapi' else object())
    with pytest.raises(RuntimeError, match='Missing backend dependencies: fastapi'):
        launcher.preflight()


def test_missing_sumo_has_actionable_error(monkeypatch):
    monkeypatch.setattr(launcher.importlib.util, 'find_spec', lambda name: object())
    monkeypatch.setattr(launcher.shutil, 'which', lambda name: None)
    with pytest.raises(RuntimeError, match='SUMO executable missing from PATH'):
        launcher.preflight()


def test_occupied_port_never_sends_cleanup_to_existing_server(monkeypatch):
    monkeypatch.setattr(launcher, 'preflight', lambda: None)
    def unexpected(*args, **kwargs):
        pytest.fail('Occupied-port startup must not issue HTTP requests or launch children')
    monkeypatch.setattr(launcher, 'urlopen', unexpected)
    monkeypatch.setattr(launcher.subprocess, 'Popen', unexpected)
    with socket.socket() as occupied:
        occupied.bind(('127.0.0.1', 0))
        occupied.listen()
        port = occupied.getsockname()[1]
        with pytest.raises(RuntimeError, match='Existing service preserved'):
            launcher.run(port, port+1 if port < 65535 else port-1, True)


def test_port_validation_precedes_startup():
    with pytest.raises(ValueError, match='distinct'):
        launcher.run(8001, 8001, True)
