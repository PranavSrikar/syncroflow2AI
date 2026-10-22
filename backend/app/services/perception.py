"""Optional YOLO/ByteTrack perception. No detector output is synthesized.

Pixel footpoints are mapped to a shared metre coordinate system only with an
explicit homography. Uncalibrated queues/waits remain pixel observations.
"""
from collections import Counter
from math import hypot, isfinite
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator

Point = tuple[float, float]
Direction = Literal['north', 'south', 'east', 'west']
CLASSES = {1: 'bicycle', 2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}


class Region(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra='forbid')
    approach: Direction
    polygon: list[Point] = Field(min_length=3)
    line: tuple[Point, Point] | None = None
    line_direction: Literal[-1, 0, 1] = 0
    area_m2: float | None = Field(default=None, gt=0)
    stop_point_m: Point | None = None

    @model_validator(mode='after')
    def geometry(self):
        area = sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(self.polygon, self.polygon[1:]+self.polygon[:1]))
        if abs(area) < 1e-6 or (self.line and self.line[0] == self.line[1]):
            raise ValueError('Degenerate region/line')
        return self


class CameraConfig(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra='forbid')
    id: str = Field(min_length=1, max_length=80)
    source: str | int
    live: bool = False
    weights: str
    regions: list[Region] = Field(min_length=1)
    homography: list[list[float]] | None = None
    world_frame: str | None = None
    overlap_group: str | None = None
    time_offset_sec: float = 0
    confidence: float = Field(default=0.25, ge=0.01, le=1)
    stationary_mps: float = Field(default=0.3, gt=0)
    stationary_pixels_per_sec: float = Field(default=2.0, gt=0)
    stopped_after_sec: float = Field(default=2.0, gt=0)
    track_gap_sec: float = Field(default=2.0, gt=0)

    @model_validator(mode='after')
    def calibration(self):
        if self.homography is not None:
            h = np.array(self.homography)
            if h.shape != (3, 3) or abs(np.linalg.det(h)) < 1e-10 or not self.world_frame:
                raise ValueError('Homography must be invertible 3x3 with a shared world_frame in metres')
        if len({r.approach for r in self.regions}) != len(self.regions):
            raise ValueError('Use one region per approach per camera')
        return self


def inside(point, polygon):
    x, y = point
    result = False
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        if (a[1] > y) != (b[1] > y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
            result = not result
    return result


def crosses(previous, point, line, direction):
    a, b = line
    side = lambda p: (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
    p, q = side(previous), side(point)
    if not ((p < 0 <= q) or (p > 0 >= q)):
        return False
    if direction and (1 if q > p else -1) != direction:
        return False
    # Crossing the infinite extension of a counting line is not a crossing.
    t = p/(p-q)
    hit = (previous[0]+t*(point[0]-previous[0]), previous[1]+t*(point[1]-previous[1]))
    u = ((hit[0]-a[0])*(b[0]-a[0])+(hit[1]-a[1])*(b[1]-a[1])) / ((b[0]-a[0])**2+(b[1]-a[1])**2)
    return 0 <= u <= 1


class CameraMeasurements:
    def __init__(self, config: CameraConfig):
        self.config = config
        self.tracks = {}
        self.counts = Counter()
        self.region_entries = Counter()
        self.last_time = None

    def world(self, point):
        if self.config.homography is None:
            return None
        p = np.asarray(self.config.homography) @ np.array([*point, 1.0])
        if abs(p[2]) < 1e-9:
            return None
        return (float(p[0]/p[2]), float(p[1]/p[2]))

    def update(self, detections, timestamp):
        if not isfinite(timestamp) or (self.last_time is not None and timestamp <= self.last_time):
            raise ValueError('Camera timestamps must be finite and strictly increasing')
        self.last_time = timestamp
        cfg = self.config
        self.tracks = {k: v for k, v in self.tracks.items() if timestamp-v['time'] <= cfg.track_gap_sec}
        observations, events = [], []
        for detection in detections:
            track_id, cls, confidence, box = detection
            if cls not in CLASSES or confidence < cfg.confidence:
                continue
            point = ((box[0]+box[2])/2, box[3])
            world = self.world(point)
            previous = self.tracks.get(track_id)
            speed, wait = None, 0.0
            counted = previous['counted'] if previous else set()
            regions_seen = previous['regions_seen'] if previous else set()
            if previous:
                dt = timestamp-previous['time']
                metric = world is not None and previous['world'] is not None
                p, q = (world, previous['world']) if metric else (point, previous['point'])
                speed = hypot(p[0]-q[0], p[1]-q[1])/dt
                threshold = cfg.stationary_mps if metric else cfg.stationary_pixels_per_sec
                if speed <= threshold:
                    wait = previous['wait'] + dt
            state = dict(point=point, world=world, time=timestamp, wait=wait, counted=counted, regions_seen=regions_seen)
            self.tracks[track_id] = state
            for region in cfg.regions:
                if previous and region.line and region.approach not in counted and crosses(previous['point'], point, region.line, region.line_direction):
                    counted.add(region.approach)
                    self.counts[region.approach] += 1
                    events.append(dict(cameraId=cfg.id, trackId=str(track_id), approach=region.approach,
                                       timestamp=timestamp, worldPoint=world, vehicleClass=CLASSES[cls]))
                if inside(point, region.polygon):
                    if region.approach not in regions_seen:
                        regions_seen.add(region.approach)
                        self.region_entries[region.approach] += 1
                    observations.append(dict(cameraId=cfg.id, trackId=str(track_id), approach=region.approach,
                        vehicleClass=CLASSES[cls], confidence=float(confidence), pixelPoint=point, worldPoint=world,
                        speed=speed, speedUnit='m/s' if world is not None else 'pixel/s',
                        observedWaitSec=wait, queued=wait >= cfg.stopped_after_sec))
        rows = {}
        for region in cfg.regions:
            items = [o for o in observations if o['approach'] == region.approach]
            queued = [o for o in items if o['queued']]
            lengths = [hypot(o['worldPoint'][0]-region.stop_point_m[0], o['worldPoint'][1]-region.stop_point_m[1])
                       for o in queued if o['worldPoint'] is not None and region.stop_point_m is not None]
            rows[region.approach] = dict(vehicles=len(items), queued=len(queued), lineCrossings=self.counts[region.approach],
                regionUniqueTrackEntries=self.region_entries[region.approach],
                classes=dict(Counter(o['vehicleClass'] for o in items)),
                queueLengthM=max(lengths) if lengths else (0.0 if cfg.homography is not None and region.stop_point_m and not queued else None),
                densityVehiclesPerM2=len(items)/region.area_m2 if region.area_m2 else None,
                maxObservedWaitSec=max((o['observedWaitSec'] for o in items), default=0.0),
                confidence=sum(o['confidence'] for o in items)/len(items) if items else None)
        return dict(cameraId=cfg.id, source='camera_yolo_bytetrack', timestamp=timestamp, approaches=rows,
                    tracks=observations, crossingEvents=events, calibrated=cfg.homography is not None,
                    limitations='Visible tracks only; wait is continuous observed stationary time; IDs may change after occlusion; detector confidence is not count accuracy')


class VideoPipeline:
    """One detector/tracker per camera, preserving IDs between consecutive frames."""
    def __init__(self, config: CameraConfig):
        self.config = config
        self.measurements = CameraMeasurements(config)

    def frames(self, stop=None, max_frames=None):
        cfg = self.config
        # Never silently download/replace weights at runtime.
        if not Path(cfg.weights).is_file():
            raise ValueError('Configured pretrained weights file is missing')
        import cv2
        from ultralytics import YOLO
        from time import time
        model = YOLO(cfg.weights)
        cap = cv2.VideoCapture()
        try:
            if isinstance(cfg.source, str) and '://' in cfg.source:
                opened = cap.open(cfg.source, cv2.CAP_FFMPEG, [cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000, cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000])
            else:
                opened = cap.open(cfg.source)
            if not opened:
                raise ValueError('Unable to open configured camera/video')
            fps = cap.get(cv2.CAP_PROP_FPS)
            if not cfg.live and (not isfinite(fps) or fps <= 0):
                raise ValueError('Recorded video requires valid FPS')
            index = 0
            while not stop or not stop.is_set():
                ok, frame = cap.read()
                if not ok:
                    if cfg.live:
                        raise ValueError('Live camera disconnected')
                    break
                timestamp = (time() if cfg.live else index/fps) + cfg.time_offset_sec
                result = model.track(frame, persist=True, tracker='bytetrack.yaml', classes=list(CLASSES),
                                     conf=cfg.confidence, device='cpu', verbose=False)[0]
                boxes = result.boxes
                detections = [] if boxes.id is None else list(zip(boxes.id.int().tolist(), boxes.cls.int().tolist(), boxes.conf.tolist(), boxes.xyxy.tolist()))
                yield self.measurements.update(detections, timestamp)
                index += 1
                if max_frames is not None and index >= max_frames:
                    break
        finally:
            cap.release()


def fuse_frames(frames, configs, distance_m=1.5, tolerance_sec=0.2):
    """Conservative one-to-one association across calibrated overlapping cameras.

Never merge same-camera tracks. Uncalibrated overlap uses a single primary
camera per approach, avoiding additive duplicates but reporting partial coverage.
"""
    clusters, warnings = [], []
    groups = {}
    for frame in frames:
        cfg = configs[frame['cameraId']]
        if cfg.overlap_group:
            for region in cfg.regions:
                groups.setdefault((cfg.overlap_group, region.approach), []).append((cfg, frame))
    primary_only = {}
    for key, members in groups.items():
        coordinate_frames = {c.world_frame for c, _ in members}
        times = [f['timestamp'] for _, f in members]
        if (any(c.homography is None or any(t['worldPoint'] is None for t in f['tracks']) for c, f in members) or len(coordinate_frames) != 1
                or max(times)-min(times) > tolerance_sec):
            primary_only[key] = min(c.id for c, _ in members)
            warnings.append('Uncalibrated or unsynchronized overlap: primary camera only; coverage partial')
    for frame in sorted(frames, key=lambda f: f['cameraId']):
        cfg = configs[frame['cameraId']]
        for item in frame['tracks']:
            row = {**item, 'timestamp': frame['timestamp'], 'worldFrame': cfg.world_frame, 'overlapGroup': cfg.overlap_group}
            primary = primary_only.get((cfg.overlap_group, row['approach']))
            if primary and primary != cfg.id:
                continue
            matches = []
            for cluster in clusters:
                if any(x['cameraId'] == row['cameraId'] for x in cluster):
                    continue
                other = cluster[0]
                if (cfg.overlap_group and cfg.overlap_group == other['overlapGroup'] and cfg.world_frame
                    and cfg.world_frame == other['worldFrame'] and row['worldPoint'] is not None and other['worldPoint'] is not None
                    and row['approach'] == other['approach'] and row['vehicleClass'] == other['vehicleClass']
                    and abs(row['timestamp']-other['timestamp']) <= tolerance_sec):
                    distance = hypot(row['worldPoint'][0]-other['worldPoint'][0], row['worldPoint'][1]-other['worldPoint'][1])
                    if distance <= distance_m:
                        matches.append((distance, cluster))
            if matches:
                min(matches, key=lambda x: x[0])[1].append(row)
            else:
                clusters.append([row])
    unique = [max(cluster, key=lambda x: x['confidence']) for cluster in clusters]
    approaches = {d: dict(vehicles=sum(r['approach'] == d for r in unique),
                          queued=sum(r['approach'] == d and r['queued'] for r in unique),
                          classes=dict(Counter(r['vehicleClass'] for r in unique if r['approach'] == d)))
                  for d in {r.approach for f in frames for r in configs[f['cameraId']].regions}}
    # Cumulative line counts use a single authority per declared overlap group.
    # This avoids adding repeat crossings without claiming cross-camera ReID.
    counting_authorities = {}
    for frame in sorted(frames, key=lambda f: f['cameraId']):
        cfg = configs[frame['cameraId']]
        for direction, row in frame['approaches'].items():
            key = (cfg.overlap_group or cfg.id, direction)
            counting_authorities.setdefault(key, (cfg.id, row['lineCrossings']))
    for direction, row in approaches.items():
        authorities = {camera: count for (_, d), (camera, count) in counting_authorities.items() if d == direction}
        row['lineCrossings'] = sum(authorities.values())
        row['countingAuthorities'] = authorities
    return dict(source='camera_fusion', approaches=approaches, tracks=unique, warnings=sorted(set(warnings)),
                associations=[[(r['cameraId'], r['trackId']) for r in c] for c in clusters],
                countingLimitations='Session counts per camera; one authority per overlap; primary changes can reset totals; no non-overlapping re-identification')
