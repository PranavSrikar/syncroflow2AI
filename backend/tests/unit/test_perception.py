"""Geometry tests use explicit fixture tracks, not purported AI detections."""
import pytest
from app.services.perception import CameraConfig, CameraMeasurements, crosses, fuse_frames
from app.services.camera_runtime import CameraRuntime


def config(id='a', calibrated=True, **kwargs):
    return CameraConfig(id=id, source='missing.mp4', weights='missing.pt',
        regions=[dict(approach='north', polygon=[(0, 0), (100, 0), (100, 100), (0, 100)],
                      line=[(0, 50), (100, 50)], area_m2=100, stop_point_m=(5, 5))],
        homography=[[0.1, 0, 0], [0, 0.1, 0], [0, 0, 1]] if calibrated else None,
        world_frame='junction' if calibrated else None, **kwargs)


def detection(id=1, x=20, y=20):
    return (id, 2, .9, [x-5, y-10, x+5, y])


def test_tracking_counting_queue_wait_and_units():
    m = CameraMeasurements(config())
    first = m.update([detection()], 0)
    assert first['approaches']['north']['vehicles'] == 1
    assert first['tracks'][0]['speed'] is None
    m.update([detection()], 1)
    stopped = m.update([detection()], 2)
    row = stopped['approaches']['north']
    assert row['queued'] == 1 and row['maxObservedWaitSec'] == 2
    assert row['regionUniqueTrackEntries'] == 1
    assert row['queueLengthM'] > 0 and row['densityVehiclesPerM2'] == .01
    crossed = m.update([detection(y=60)], 3)
    assert crossed['approaches']['north']['lineCrossings'] == 1
    assert crossed['tracks'][0]['observedWaitSec'] == 0
    m.update([detection(y=20)], 4)
    assert m.update([detection(y=60)], 5)['approaches']['north']['lineCrossings'] == 1
    assert m.update([], 6)['approaches']['north']['vehicles'] == 0


def test_finite_line_direction_gap_and_missing_calibration():
    assert crosses((20, 20), (20, 80), ((0, 50), (100, 50)), 1)
    assert not crosses((120, 20), (120, 80), ((0, 50), (100, 50)), 0)
    assert not crosses((20, 20), (20, 80), ((0, 50), (100, 50)), -1)
    m = CameraMeasurements(config(calibrated=False))
    m.update([detection()], 0)
    row = m.update([detection(y=60)], 4)
    assert row['approaches']['north']['lineCrossings'] == 0  # long occlusion resets history
    assert row['approaches']['north']['queueLengthM'] is None
    assert row['tracks'][0]['speedUnit'] == 'pixel/s'
    with pytest.raises(ValueError):
        m.update([], 4)


def test_config_rejects_bad_homography():
    with pytest.raises(ValueError):
        config().model_copy().model_validate({**config().model_dump(), 'homography': [[0, 0, 0]]*3})


def test_cross_camera_association_one_to_one_time_and_class_gates():
    a, b = config('a', overlap_group='overlap'), config('b', overlap_group='overlap')
    f1 = CameraMeasurements(a).update([detection(1), detection(2, x=40)], 0)
    f2 = CameraMeasurements(b).update([detection(10), detection(20, x=40)], 0.05)
    fused = fuse_frames([f1, f2], {'a': a, 'b': b})
    assert fused['approaches']['north']['vehicles'] == 2
    assert all(len(c) == 2 for c in fused['associations'])
    f2['timestamp'] = 2
    fallback = fuse_frames([f1, f2], {'a': a, 'b': b})
    assert fallback['approaches']['north']['vehicles'] == 2
    assert fallback['warnings']  # out-of-sync overlap is never blindly summed


def test_uncalibrated_overlap_uses_primary_instead_of_adding_duplicates():
    a, b = config('a', False, overlap_group='overlap'), config('b', False, overlap_group='overlap')
    frames = [CameraMeasurements(c).update([detection()], 0) for c in (a, b)]
    fused = fuse_frames(frames, {'a': a, 'b': b})
    assert fused['approaches']['north']['vehicles'] == 1
    assert fused['warnings']


def test_missing_camera_fallback_and_worker_failure():
    runtime = CameraRuntime()
    assert runtime.snapshot()['available'] is False
    runtime.start([config()])
    runtime.workers['a'][1].join(10)
    snapshot = runtime.snapshot()
    assert not snapshot['available']
    assert snapshot['cameras']['a']['state'] == 'failed'
    assert 'weights' in snapshot['cameras']['a']['error']
    runtime.stop()


def test_classes_and_stale_frames_are_explicit():
    from time import monotonic
    cfg = config()
    measurements = CameraMeasurements(cfg)
    frame = measurements.update([(i, cls, .8, [10*i, 0, 10*i+5, 20]) for i, cls in enumerate((1, 2, 3, 5, 7), 1)], 0)
    assert set(frame['approaches']['north']['classes']) == {'bicycle', 'car', 'motorcycle', 'bus', 'truck'}
    runtime = CameraRuntime()
    runtime.configs = {'a': cfg}
    runtime.status = {'a': dict(state='running', error=None)}
    runtime.frames = {'a': (frame, monotonic()-4)}
    assert not runtime.snapshot()['available']


def test_missing_approach_is_unavailable_instead_of_false_zero():
    a = config('a')
    b = config('b').model_dump()
    b['regions'][0]['approach'] = 'east'
    b = CameraConfig.model_validate(b)
    frame = CameraMeasurements(a).update([detection()], 0)
    from time import monotonic
    runtime = CameraRuntime()
    runtime.configs = {'a': a, 'b': b}
    runtime.frames = {'a': (frame, monotonic())}
    runtime.status = {'a': dict(state='running', error=None), 'b': dict(state='failed', error='fixture unavailable')}
    result = runtime.snapshot()
    assert result['available'] and result['partialCoverage']
    assert result['unavailableApproaches'] == ['east']
    assert 'east' not in result['fused']['approaches']
