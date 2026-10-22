> Historical milestone record. FINAL_DEMO_REPORT.md supersedes current status and documents the Stage 3 occupancy correction; earlier weights/performance observations are not current validation.

# Stage 1 perception and forecasting — 2026-10-22

This extends the existing prototype. SUMO remains the default operational measurement source. Existing signal supervisors, pedestrian clearance, emergency priority and disabled learned-policy gate remain in place.

## Implemented behavior

- Optional CPU YOLO11n pretrained vehicle detection, ByteTrack persistent IDs, recorded files and optional device/RTSP input. Supported COCO classes: bicycle, car, motorcycle, bus, truck. Auto-rickshaws and other local classes are not separately supported by these weights.
- Per-approach pixel polygons, finite directed counting lines, instantaneous region counts, unique region track entries and once-per-track line crossings. Footpoint motion estimates visible stationary time and halted counts. Occlusion/ID switches can reset time and duplicate cumulative track counts.
- Optional invertible pixel-to-ground homography in metres, measured region area and stop point. These enable metric speed, density and furthest-visible-stopped-vehicle queue distance. Without calibration, speed is explicitly pixels/s, queue distance/density are unavailable unless the required metric information is supplied. Counts do not imply unseen traffic is absent.
- Camera workers expose fresh observations, failures, EOF and stale last frames. Frames older than three seconds or from stopped/failed/EOF cameras cannot be selected as live traffic state. Missing cameras fall back to connected SUMO, otherwise unavailable. Partial camera coverage explicitly marks unobserved approaches unavailable instead of emitting zero counts. Recorded workers replay at source FPS without looping; the offline CLI runs as fast as possible.
- Calibrated, synchronized overlap uses distance/class/approach-gated one-to-one association, never merging two tracks from the same camera. Shared `world_frame`, `overlap_group` and synchronized timestamps are required. Incompatible or unsynchronized overlap uses one primary camera per approach, with partial-coverage warnings. Cumulative line counts use one authority per overlap group. Primary changes can reset totals. This is geometric association, not appearance ReID or a guarantee against close-vehicle ambiguity. All potentially overlapping cameras must be declared in the same group.
- Historical CSV validation, atomic replacement, timezone-aware timestamps, finite nonnegative PCU arrivals and interval validation; rejects duplicate/overlapping intervals. Missing rainfall is allowed. Future/incomplete and stale history is excluded.
- Deterministic weekday/half-hour seasonal mean, shrunk toward approach mean, in ten-second forecast bins. Rain effect is estimated only with sufficient wet/dry history; otherwise no demand effect is invented. Rain, monsoon season and missing weather widen heuristic intervals. Confidence labels and bounds are diagnostic, not calibrated probabilities.
- Manual weather ingestion or explicit Open-Meteo refresh with five-second timeout and verified system TLS trust. No credentials required for the configured public endpoint. Provider outages retain only time-valid cached weather; stale weather becomes missing. Network access never occurs in the MPC solve.
- Forecast mean arrival trajectories feed existing constrained MPC in PCU/s. Missing approaches use recent observed arrivals. Existing optimization timeout/Max-Pressure fallback and supervisors remain authoritative. Uncertainty bounds are reported; MPC does not perform robust uncertainty optimization or rain-dependent saturation calibration.
- Dashboard displays camera health/counts/classes through API diagnostics, queues/waits, calibration availability, fused counts and forecast rate/range/confidence. Observation selector defaults to SUMO. Forecast enable/disable preserves provider settings. Existing synthetic tabs remain demonstrations.

## Camera operation

Install optional dependencies using the existing environment:

```powershell
.\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements-perception.txt
```

The verified environment uses torch 2.14.1+cpu and torchvision 0.29.1. Install compatible torch/torchvision builds for another host. Core backend imports do not require OpenCV, Ultralytics or torch. Do not train or silently replace detector weights.

Actual verification assets were downloaded to `.checkpoints/perception`:

- [YOLO11n weights](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt)
- [Road vehicle sample](https://media.roboflow.com/supervision/video-examples/vehicles.mp4)
- [Ultralytics tracker interface](https://docs.ultralytics.com/modes/track/)

The 3840×2160 road sample has 538 frames at 25 FPS. Its example mapping to `north` is a test label, not a surveyed junction approach. The example has no physical calibration. The airport and pedestrian demo downloads are exploratory assets; the road sample is the actual pipeline verification fixture. Preserve/download assets separately; source archives exclude generated weights/videos.

From the project root:

```powershell
.\backend\.venv\Scripts\python.exe scripts/perceive_video.py --config backend/examples/camera-road.example.json --output .checkpoints/perception/road-inference.jsonl --max-frames 60
```

For backend camera mode, create a JSON **array** of camera configs (the CLI above takes one object). Use absolute local paths; relative paths resolve against the process working directory. Set `SYNCHROFLOW_CAMERA_CONFIG` before launching the backend. The generated `.checkpoints/perception/cameras-api.json` contains absolute paths for this workspace. Then use Start cameras / Configured cameras in the dashboard, or:

```powershell
$env:SYNCHROFLOW_CAMERA_CONFIG=(Resolve-Path '.checkpoints/perception/cameras-api.json').Path
.\backend\.venv\Scripts\python.exe scripts/run_dev.py
```

Start/stop routes: `POST /api/v1/perception/start`, `/perception/stop`. Inspect `GET /api/v1/perception/status` and `/api/v1/traffic-state?source=camera`. Browser requests cannot supply arbitrary source or weight paths. Each worker has its own detector/tracker. CPU inference is used for reproducibility. Set `source` to integer `0` and `live: true` for a local webcam, or an operator-configured RTSP URL. Live timestamps use epoch seconds; recorded timestamps use frame index/FPS plus `time_offset_sec`. Do not mix clock domains in an overlap group. RTSP open/read timeouts are five seconds; a stuck native device driver may require restarting the process. Live hardware/RTSP is implemented but unverified here.

Calibration procedure: survey at least four non-collinear ground points, compute a homography mapping original-resolution pixel footpoints to a common metre frame; configure `homography`, `world_frame`, approach `polygon`, `area_m2`, `stop_point_m`, and finite `line`. Set `overlap_group` for overlapping cameras, synchronize clocks/recording offsets, then verify projected distances and association against manually labeled footage. Calibrate stopped thresholds, detector accuracy and line direction. Distorted/non-planar views require camera correction before relying on metric estimates. No site calibration was provided.

Camera mode supplies traffic observations only. It does not control real signals or replace SUMO pedestrian, signal-state or internal-occupancy safety observations. Road-camera actuation requires an independently verified full safety observation and actuation interface.

## History and weather operation

History CSV schema: `timestamp,approach,arrivals_pcu,interval_sec,rainfall_mm_h` (rainfall optional). Timestamp is interval **start** with UTC offset; intervals must be complete. Approaches are north/south/east/west. Convert classified counts to calibrated PCU totals before ingestion; vehicle counts and PCU are not interchangeable. Default history retention is 56 days; operational timestamps use Asia/Kolkata weekday/time bins. State is process-local: reload history/config after restart.

Example data is explicitly artificial. Generate a deterministic sample with `scripts/make_example_history.py`; its default as-of time is 2026-10-22 UTC. Change `--as-of` for another date. Load it for demonstration:

```powershell
$base='http://127.0.0.1:8001/api/v1'
$payload=@{ csv=(Get-Content backend/examples/history.EXAMPLE.csv -Raw); example_data=$true } | ConvertTo-Json
Invoke-RestMethod "$base/forecast/history" -Method Post -ContentType 'application/json' -Body $payload
Invoke-RestMethod "$base/forecast/config" -Method Post -ContentType 'application/json' -Body '{"enabled":true,"weather_provider":"open_meteo","latitude":19.076,"longitude":72.878}'
Invoke-RestMethod "$base/forecast/weather/refresh" -Method Post
Invoke-RestMethod "$base/forecast"
```

Example forecasts are blocked from MPC by default. Only deliberate tests may set `allow_example_for_mpc: true`. Genuine history should be uploaded with `example_data: false`; that flag is operator provenance, not an authenticity verifier. No real historical dataset was supplied. Manual weather: `POST /forecast/weather` with `timestamp`, `rainfall_mm_h`, `source`; configure `weather_provider: manual`. `POST /forecast/enabled?enabled=false` disables forecasting without resetting other settings. `GET /forecast?at=<offset-aware ISO time>&horizon_sec=60` supports reproducible queries. Settings endpoint replaces configuration; omitted fields revert to defaults.

SUMO forecast time anchors to wall-clock UTC at simulation start plus simulated seconds, rather than treating SUMO seconds as calendar epochs. Replayed historic scenarios need their own configured data/time alignment before performance evaluation. Live weather can expire when accelerated simulation advances beyond it. Rainfall conversion follows the provider's accumulation interval: [Open-Meteo current-condition documentation](https://open-meteo.com/en/docs).

## Verification and remaining validation

Before modification: all 61 backend tests passed; build, TypeScript and eight frontend groups passed. Latest pre-change archive matched all 136 source hashes; separate recovery copy also verified. No Git executable or `.git` directory was available; no history was initialized or replaced.

Real offline run: 60 frames, 260 tracked observations, 13 unique track IDs. JSONL is `.checkpoints/perception/road-inference.jsonl`. Detection confidence is emitted per track; it is not a measured counting accuracy. Live Open-Meteo refresh also succeeded (0.0 mm/h in its returned snapshot). Initial certificate failure was corrected using the system trust store without disabling TLS verification.

Final regression: **83 passed in 193.06 s**, one existing Starlette warning; actual Edge browser: **2 passed in 23.1 s**. Build, TypeScript, eight frontend groups, startup smoke and pip check pass. All original SUMO networks retain their pre-change SHA-256 hashes. Recovery source/artifact archives and separate copies are listed in `.checkpoints/STAGE1_RECOVERY.json`. See TEST_RESULTS.md for full details. Real-video tests are opt-in when assets are absent; they were explicitly enabled for this sprint:

```powershell
$env:DEBUG='false'
$env:SYNCHROFLOW_TEST_VIDEO=(Resolve-Path '.checkpoints/perception/road.mp4').Path
$env:SYNCHROFLOW_TEST_WEIGHTS=(Resolve-Path '.checkpoints/perception/yolo11n.pt').Path
cd backend
.\.venv\Scripts\python.exe -m pytest -o addopts='-ra'
```

Unit tests use declared fixture tracks/history to verify geometry and math. Actual-video tests execute pretrained inference and FastAPI workers. Real SUMO integration verifies forecast consumption and disable fallback through the supervisor. Tests do not establish detector precision/recall, wait or queue accuracy, real multi-camera association accuracy, weather response validity, forecast out-of-sample accuracy or controller improvement. Live camera hardware, surveyed calibration, real historical data and field validation are still missing. MAPPO remains disabled operationally.
