"""Deterministic, explicitly artificial CSV fixture, never operational history."""
import argparse
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='backend/examples/history.EXAMPLE.csv')
    parser.add_argument('--as-of', default='2026-10-22T00:00:00+00:00')
    args = parser.parse_args()
    end = datetime.fromisoformat(args.as_of)
    if end.tzinfo is None:
        parser.error('--as-of needs a timezone')
    with Path(args.output).open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'approach', 'arrivals_pcu', 'interval_sec', 'rainfall_mm_h'])
        for day in range(28, 0, -1):
            for hour in (2, 8, 14, 20):
                at = (end-timedelta(days=day)).replace(hour=hour)
                rain = 12 if day % 3 == 0 else 0
                for index, direction in enumerate(('north', 'south', 'east', 'west')):
                    amount = (6+index*2+(4 if hour in (2, 14) else 0))*(0.8 if rain else 1)
                    writer.writerow([at.isoformat(), direction, amount, 60, rain])
    print('EXAMPLE ONLY:', args.output)


if __name__ == '__main__':
    main()
