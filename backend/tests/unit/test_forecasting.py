from datetime import datetime, timedelta, timezone
import pytest
from app.services.forecasting import ForecastService, ForecastSettings, Weather
from app.services.constrained_mpc import ConstrainedMPC

AT = datetime(2026, 10, 22, 8, tzinfo=timezone.utc)


def history(at=AT):
    lines = ['timestamp,approach,arrivals_pcu,interval_sec,rainfall_mm_h']
    for day in range(1, 29):
        for direction in ('north', 'south', 'east', 'west'):
            lines.append(f'{(at-timedelta(days=day)).isoformat()},{direction},{12 if day%2 else 6},60,{0 if day%2 else 10}')
    return '\n'.join(lines)


def service(example=False):
    s = ForecastService()
    s.configure(ForecastSettings(enabled=True, weather_provider='manual'))
    s.ingest_csv(history(), example=example)
    return s


def test_history_baseline_reproducible_uncertainty_and_weather():
    s = service()
    dry_missing = s.predict(AT)
    assert dry_missing == s.predict(AT)
    assert dry_missing['available'] and not dry_missing['weatherAvailable']
    s.set_weather(Weather(timestamp=AT, rainfall_mm_h=0, source='fixture'))
    dry = s.predict(AT)['approaches']['north']['steps'][0]
    s.set_weather(Weather(timestamp=AT, rainfall_mm_h=30, source='fixture'))
    wet = s.predict(AT)['approaches']['north']['steps'][0]
    assert wet['weatherAdjusted']
    assert wet['arrivalRatePcuPerSec'] < dry['arrivalRatePcuPerSec']
    assert wet['upperPcuPerSec']-wet['lowerPcuPerSec'] > dry['upperPcuPerSec']-dry['lowerPcuPerSec']
    assert s.predict(AT+timedelta(hours=2))['weatherAvailable'] is False


def test_missing_disabled_example_future_and_stale_fallbacks():
    s = ForecastService()
    assert not s.predict(AT)['available']
    s = service(True)
    assert s.predict(AT)['available']
    assert not s.predict(AT, for_mpc=True)['available']
    assert not s.predict(AT-timedelta(days=60))['available']
    assert not s.predict(AT+timedelta(days=100))['available']
    s.configure(ForecastSettings(enabled=False))
    assert not s.predict(AT)['available']


@pytest.mark.parametrize('csv', [
    'wrong,header\n1,2',
    'timestamp,approach,arrivals_pcu,interval_sec\n2026-10-01,north,2,60',
    'timestamp,approach,arrivals_pcu,interval_sec\n2026-10-01T00:00:00Z,north,-1,60',
    'timestamp,approach,arrivals_pcu,interval_sec\n2026-10-01T00:00:00Z,north,nan,60',
])
def test_bad_history_is_rejected_atomically(csv):
    s = service()
    before = s.predict(AT)
    with pytest.raises(ValueError):
        s.ingest_csv(csv)
    assert s.predict(AT) == before


def test_duplicate_and_overlap_rejected():
    s = service()
    data = history()
    with pytest.raises(ValueError):
        s.ingest_csv(data+'\n'+data.splitlines()[1])


def test_mpc_time_varying_arrival_mass_conservation():
    mpc = object.__new__(ConstrainedMPC)
    rates = [0.0]*30+[0.4]*30
    _, trajectory = mpc.rollout({'north': 0.0}, {'north': rates}, {'north': 0.0}, {0: {'north'}, 3: set()}, 0, 10, 10)
    assert trajectory[29]['north'] == 0
    assert abs(trajectory[-1]['north']-12) < 1e-8


def test_weekday_and_time_bins_change_the_prediction():
    s = ForecastService()
    s.configure(ForecastSettings(enabled=True))
    rows = ['timestamp,approach,arrivals_pcu,interval_sec']
    for week in range(1, 5):
        date = AT-timedelta(days=7*week)
        rows.extend([f'{date.isoformat()},north,30,60', f'{(date+timedelta(hours=3)).isoformat()},north,3,60'])
    s.ingest_csv('\n'.join(rows))
    rate = lambda at: s.predict(at)['approaches']['north']['steps'][0]['arrivalRatePcuPerSec']
    assert rate(AT) > rate(AT+timedelta(hours=3))
    assert rate(AT) > rate(AT+timedelta(days=1))


def test_weather_provider_conversion_and_outage(monkeypatch):
    import httpx
    s = service()
    s.configure(ForecastSettings(enabled=True, weather_provider='open_meteo', latitude=19, longitude=72))
    def response(*args, **kwargs):
        return httpx.Response(200, request=httpx.Request('GET', args[0]), json={
            'current': {'time': '2026-10-22T08:00', 'precipitation': 2, 'interval': 900}})
    monkeypatch.setattr(httpx, 'get', response)
    assert s.refresh_weather()['rainfall_mm_h'] == 8
    def outage(*args, **kwargs):
        raise httpx.ConnectTimeout('fixture outage')
    monkeypatch.setattr(httpx, 'get', outage)
    assert not s.refresh_weather()['available']
    result = s.predict(AT+timedelta(hours=2))
    assert result['available'] and not result['weatherAvailable']
    assert result['weatherError']
