"""Background video workers; stale/failed inputs never masquerade as live data."""
from copy import deepcopy
from threading import Event, RLock, Thread
from time import monotonic

from app.services.perception import CameraConfig, VideoPipeline, fuse_frames


class CameraRuntime:
    def __init__(self):
        self.lock = RLock()
        self.workers = {}
        self.configs = {}
        self.frames = {}
        self.status = {}

    def start(self, configs: list[CameraConfig]):
        if not configs or len({c.id for c in configs}) != len(configs):
            raise ValueError('Nonempty, unique camera IDs required')
        self.stop()
        with self.lock:
            self.configs = {c.id: c for c in configs}
            self.frames = {}
            self.status = {c.id: dict(state='starting', error=None) for c in configs}
            for config in configs:
                stop = Event()
                worker = Thread(target=self._run, args=(config, stop), daemon=True, name='camera-'+config.id)
                self.workers[config.id] = (stop, worker)
                worker.start()
        return self.snapshot()

    def _run(self, config, stop):
        try:
            started, first = monotonic(), None
            count = 0
            for frame in VideoPipeline(config).frames(stop):
                if stop.is_set():
                    break
                # Replay recorded footage at source speed (never a simulated live camera).
                if first is None:
                    first = frame['timestamp']
                    started = monotonic()
                if not config.live and stop.wait(max(0, frame['timestamp']-first-(monotonic()-started))):
                    break
                with self.lock:
                    self.frames[config.id] = (frame, monotonic())
                    self.status[config.id] = dict(state='running', error=None)
                count += 1
            with self.lock:
                self.status[config.id] = dict(state='stopped' if stop.is_set() else 'eof', error=None if count else 'No frames decoded')
        except Exception as exc:
            with self.lock:
                self.status[config.id] = dict(state='failed', error=str(exc))

    def stop(self):
        with self.lock:
            workers = list(self.workers.values())
            for event, _ in workers:
                event.set()
        for _, thread in workers:
            thread.join(timeout=6)
        with self.lock:
            if any(thread.is_alive() for _, thread in workers):
                raise RuntimeError('Camera worker still stopping; retry before restarting')
            self.workers = {}
            for status in self.status.values():
                status['state'] = 'stopped'

    def snapshot(self):
        with self.lock:
            fresh = [frame for key, (frame, received) in self.frames.items()
                     if monotonic()-received <= 3 and self.status[key]['state'] == 'running']
            cameras = {key: {**value, 'fresh': any(f['cameraId'] == key for f in fresh),
                            'lastFrame': self.frames[key][0] if key in self.frames else None}
                       for key, value in self.status.items()}
            result = dict(available=bool(fresh), cameras=cameras,
                          fused=fuse_frames(fresh, self.configs) if fresh else None,
                          fallback=None if fresh else 'No fresh camera observations; use SUMO when connected, otherwise unavailable',
                          mode='observation_only', actuationEnabled=False)
            covered = {region.approach for frame in fresh for region in self.configs[frame['cameraId']].regions}
            configured = {region.approach for config in self.configs.values() for region in config.regions}
            result['unavailableApproaches'] = sorted(configured-covered)
            result['partialCoverage'] = bool(configured-covered)
            return deepcopy(result)


camera_runtime = CameraRuntime()
