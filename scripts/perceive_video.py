"""Execute real inference; write one JSON object per processed frame."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.services.perception import CameraConfig, VideoPipeline


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True, help='JSON object for one camera')
    parser.add_argument('--output', required=True)
    parser.add_argument('--max-frames', type=int, default=None)
    args = parser.parse_args()
    config = CameraConfig.model_validate_json(Path(args.config).read_text(encoding='utf-8'))
    count = detections = 0
    ids = set()
    with Path(args.output).open('w', encoding='utf-8') as output:
        for frame in VideoPipeline(config).frames(max_frames=args.max_frames):
            output.write(json.dumps(frame, allow_nan=False)+'\n')
            count += 1
            detections += len(frame['tracks'])
            ids.update(t['trackId'] for t in frame['tracks'])
    print(json.dumps(dict(frames=count, trackedObservations=detections, uniqueTrackIds=len(ids), output=args.output)))
    if not count:
        raise SystemExit('No frames decoded')


if __name__ == '__main__':
    main()
