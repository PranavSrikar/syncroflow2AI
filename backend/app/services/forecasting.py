"""Reproducible seasonal baseline in PCU/s, with explicit data provenance.

Uses same weekday and half-hour bin, shrunk to the approach mean. Empirical
spread plus sample-size/missing-weather penalties form heuristic intervals,
not calibrated probabilities. No network calls occur inside controller solves.
"""
import csv
import io
import ssl
from datetime import datetime, timedelta, timezone
from math import isfinite, sqrt
from statistics import mean, pstdev
from threading import RLock
from typing import Literal
from zoneinfo import ZoneInfo

import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.services.perception import Direction


class HistoryRow(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra='forbid')
    timestamp: datetime
    approach: Direction
    junction_id: str = Field(default='center', min_length=1, max_length=80)
    arrivals_pcu: float = Field(ge=0, le=100000)
    interval_sec: float = Field(ge=1, le=3600)
    rainfall_mm_h: float | None = Field(default=None, ge=0, le=500)


class Weather(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra='forbid')
    timestamp: datetime
    rainfall_mm_h: float = Field(ge=0, le=500)
    source: str = Field(min_length=1, max_length=100)


class ForecastSettings(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra='forbid')
    enabled: bool = False
    allow_example_for_mpc: bool = False
    timezone: str = 'Asia/Kolkata'
    max_history_age_days: int = Field(default=56, ge=1, le=366)
    weather_provider: Literal['manual', 'open_meteo', 'disabled'] = 'disabled'
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


def aware(value):
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('Timezone-aware timestamps required')
    return value


class ForecastService:
    def __init__(self):
        self.lock = RLock()
        self.settings = ForecastSettings()
        self.rows = []
        self.example = False
        self.weather = None
        self.weather_error = None

    def configure(self, settings):
        ZoneInfo(settings.timezone)
        with self.lock:
            self.settings = settings
        return self.predict()

    def ingest_csv(self, content, example=False):
        reader = csv.DictReader(io.StringIO(content))
        required = {'timestamp', 'approach', 'arrivals_pcu', 'interval_sec'}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError('CSV requires timestamp,approach,arrivals_pcu,interval_sec; optional rainfall_mm_h')
        parsed, seen = [], set()
        for record in reader:
            row = HistoryRow.model_validate({k: v for k, v in record.items() if v != ''})
            aware(row.timestamp)
            key = (row.timestamp, row.approach, row.junction_id)
            if key in seen:
                raise ValueError('Duplicate history timestamp/approach')
            seen.add(key)
            parsed.append(row)
            if len(parsed) > 100000:
                raise ValueError('Maximum 100000 history rows')
        if not parsed:
            raise ValueError('Empty history is not usable')
        # Reject overlapping aggregation intervals rather than double weighting them.
        ends = {}
        for row in sorted(parsed, key=lambda r: r.timestamp):
            key = (row.junction_id, row.approach)
            if key in ends and row.timestamp < ends[key]:
                raise ValueError('Overlapping history intervals')
            ends[key] = row.timestamp+timedelta(seconds=row.interval_sec)
        with self.lock:
            self.rows, self.example = parsed, example
        return dict(rows=len(parsed), exampleData=example, units='PCU/s', replaced=True)

    def set_weather(self, weather):
        aware(weather.timestamp)
        with self.lock:
            self.weather = weather
            self.weather_error = None

    def refresh_weather(self):
        with self.lock:
            config = self.settings.model_copy()
        if config.weather_provider != 'open_meteo' or config.latitude is None or config.longitude is None:
            raise ValueError('Configure open_meteo and latitude/longitude first')
        try:
            response = httpx.get('https://api.open-meteo.com/v1/forecast', params={
                'latitude': config.latitude, 'longitude': config.longitude,
                'current': 'precipitation', 'timezone': 'UTC'}, timeout=5, verify=ssl.create_default_context())
            response.raise_for_status()
            current = response.json()['current']
            # Open-Meteo current precipitation is accumulated over current.interval.
            interval = float(current['interval'])
            if not isfinite(interval) or interval <= 0:
                raise ValueError('Invalid weather interval')
            weather = Weather(timestamp=datetime.fromisoformat(current['time']).replace(tzinfo=timezone.utc),
                              rainfall_mm_h=float(current['precipitation'])*3600/interval, source='open_meteo')
            self.set_weather(weather)
            return weather.model_dump(mode='json')
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            with self.lock:
                self.weather_error = str(exc)
            return dict(available=False, error=str(exc), fallback='Missing-weather uncertainty')

    def predict(self, at=None, horizon_sec=60, for_mpc=False, junction_id='center'):
        at = aware(at or datetime.now(timezone.utc))
        with self.lock:
            cfg, history, example, weather = self.settings, self.rows[:], self.example, self.weather
            weather_error = self.weather_error
        local = at.astimezone(ZoneInfo(cfg.timezone))
        # Never use future records or stale seasonal data.
        history = [r for r in history if r.junction_id == junction_id and r.timestamp+timedelta(seconds=r.interval_sec) <= at
                   and (at-r.timestamp).total_seconds() <= cfg.max_history_age_days*86400]
        weather_ok = (cfg.weather_provider != 'disabled' and weather is not None
                      and -300 <= (at-weather.timestamp).total_seconds() <= 3600)
        rain = weather.rainfall_mm_h if weather_ok else None
        reason = ('Forecasts disabled' if not cfg.enabled else
                  'Example data blocked for MPC' if for_mpc and example and not cfg.allow_example_for_mpc else None)
        predictions = {}
        for direction in ('north', 'south', 'east', 'west'):
            rows = [r for r in history if r.approach == direction]
            if not rows or reason:
                continue
            values = [r.arrivals_pcu/r.interval_sec for r in rows]
            slots = []
            for offset in range(0, horizon_sec, 10):
                target = local+timedelta(seconds=offset)
                seasonal = [r for r in rows if (t := r.timestamp.astimezone(ZoneInfo(cfg.timezone))).weekday() == target.weekday()
                            and t.hour*2+t.minute//30 == target.hour*2+target.minute//30]
                samples = [r.arrivals_pcu/r.interval_sec for r in seasonal]
                estimate = (sum(samples)+3*mean(values))/(len(samples)+3)
                # A rain adjustment is learned only with >=3 wet and dry examples.
                wet = [r.arrivals_pcu/r.interval_sec for r in rows if r.rainfall_mm_h is not None and r.rainfall_mm_h >= 2.5]
                dry = [r.arrivals_pcu/r.interval_sec for r in rows if r.rainfall_mm_h is not None and r.rainfall_mm_h < 2.5]
                adjusted = rain is not None and rain >= 2.5 and len(wet) >= 3 and len(dry) >= 3 and mean(dry) > 0
                if adjusted:
                    estimate *= min(1.5, max(0.5, mean(wet)/mean(dry)))
                spread = max(0.02, pstdev(samples or values)) + max(0.02, estimate)/sqrt(len(samples)+1)
                # Monsoon months and intense rain widen uncertainty, not fabricated demand.
                multiplier = 1+(0.5 if rain is None else min(2, rain/10))+(0.5 if 6 <= target.month <= 9 else 0)
                width = 1.96*spread*multiplier
                slots.append(dict(offsetSec=offset, durationSec=min(10, horizon_sec-offset), arrivalRatePcuPerSec=estimate,
                                  lowerPcuPerSec=max(0, estimate-width), upperPcuPerSec=estimate+width,
                                  seasonalSamples=len(samples), weatherAdjusted=adjusted))
            predictions[direction] = dict(steps=slots, historySamples=len(rows),
                                          confidence='low' if len(rows) < 10 or not weather_ok else 'moderate')
        return dict(enabled=cfg.enabled, available=bool(predictions), junctionId=junction_id, generatedAt=at.isoformat(), horizonSec=horizon_sec,
                    source='seasonal_shrinkage_baseline', exampleData=example, units='PCU/s',
                    approaches=predictions, weatherAvailable=weather_ok, rainfallMmH=rain,
                    weatherError=weather_error, fallback=reason or (None if predictions else 'Missing/stale history; recent observed arrivals'),
                    uncertainty='Heuristic bounds, not calibrated coverage; rainfall/monsoon and missing weather widen intervals')


forecast_service = ForecastService()
