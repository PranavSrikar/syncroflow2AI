"""Opt-in real pretrained inference on recorded footage. No mocked detector."""
import importlib.util
import os
from pathlib import Path
import pytest
from app.services.perception import CameraConfig, VideoPipeline
import json
import time
from fastapi.testclient import TestClient
from app.main import app


def test_real_recorded_video_tracking():
    video = os.environ.get('SYNCHROFLOW_TEST_VIDEO')
    weights = os.environ.get('SYNCHROFLOW_TEST_WEIGHTS')
    if not video or not weights or not importlib.util.find_spec('ultralytics'):
        pytest.skip('Set SYNCHROFLOW_TEST_VIDEO and SYNCHROFLOW_TEST_WEIGHTS; install perception dependencies')
    assert Path(video).is_file() and Path(weights).is_file()
    config = CameraConfig(id='real-test', source=video, weights=weights, regions=[dict(
        approach='north', polygon=[(0, 0), (10000, 0), (10000, 10000), (0, 10000)])])
    frames = list(VideoPipeline(config).frames(max_frames=30))
    assert len(frames) == 30
    tracks = [{t['trackId'] for t in f['tracks']} for f in frames]
    assert any(tracks)
    assert any(a & b for a, b in zip(tracks, tracks[1:])), 'No persistent IDs observed'
    assert all(0 <= t['confidence'] <= 1 for f in frames for t in f['tracks'])


def test_real_camera_api_mode_and_stop_fallback(tmp_path, monkeypatch):
    video, weights = os.environ.get('SYNCHROFLOW_TEST_VIDEO'), os.environ.get('SYNCHROFLOW_TEST_WEIGHTS')
    if not video or not weights or not importlib.util.find_spec('ultralytics'):
        pytest.skip('Real video and pretrained weights required')
    config = dict(id='api-video', source=video, weights=weights, regions=[dict(
        approach='north', polygon=[(0, 0), (10000, 0), (10000, 10000), (0, 10000)])])
    path = tmp_path/'camera.json'
    path.write_text(json.dumps([config]))
    monkeypatch.setenv('SYNCHROFLOW_CAMERA_CONFIG', str(path))
    with TestClient(app) as client:
        try:
            assert client.post('/api/v1/perception/start').status_code == 200
            deadline = time.monotonic()+20
            while time.monotonic() < deadline:
                state = client.get('/api/v1/traffic-state?source=camera').json()
                if state['source'] == 'camera_fusion' and state['traffic']['tracks']:
                    break
                time.sleep(.1)
            assert state['source'] == 'camera_fusion'
            assert state['traffic']['approaches']['north']['vehicles'] > 0
            assert not state['perception']['actuationEnabled']
        finally:
            assert client.post('/api/v1/perception/stop').status_code == 200
        state = client.get('/api/v1/traffic-state?source=camera').json()
        assert state['source'] != 'camera_fusion' and state['fallback']
