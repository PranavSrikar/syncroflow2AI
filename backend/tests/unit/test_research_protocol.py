"""Scientific cache reuse must never silently mix weights or source versions."""
import json
from pathlib import Path
import pytest

pytest.importorskip('torch')


@pytest.fixture
def research(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[3]/'scripts'))
    import research_phase4
    monkeypatch.setattr(research_phase4,'OUT',tmp_path)
    def unexpected_environment(*args,**kwargs):
        raise AssertionError('Cache validation must complete before starting SUMO')
    monkeypatch.setattr(research_phase4,'MultiJunctionEnv',unexpected_environment)
    (tmp_path/'trials').mkdir()
    return research_phase4


def test_matching_cached_experiment_does_not_start_sumo(research):
    row=dict(mode='mpc',checkpointSha256=None,provenance=research.provenance(),status='completed')
    (research.OUT/'trials/selection-mpc-d1.0-s901-t300.json').write_text(json.dumps(row))
    assert research.trial('mpc',901,300,1.0,split='selection')==row


@pytest.mark.parametrize('changed',['controller','source'])
def test_stale_cache_is_rejected_before_simulation(research,changed):
    row=dict(mode='mpc',checkpointSha256=None,provenance=research.provenance())
    if changed=='controller': row['mode']='fixed_time'
    else: row['provenance']['architectureFingerprint']='stale'
    (research.OUT/'trials/selection-mpc-d1.0-s901-t300.json').write_text(json.dumps(row))
    with pytest.raises(ValueError,match='Cached trial'):
        research.trial('mpc',901,300,1.0,split='selection')


def test_same_filename_different_weights_cannot_reuse_candidate_results(research):
    folder=research.OUT/'train-21'; folder.mkdir()
    checkpoint=folder/'update-0016.pt'; checkpoint.write_bytes(b'changed weights')
    row=dict(mode='candidate',checkpointSha256='old digest',provenance=research.provenance())
    (research.OUT/'trials/selection-train-21-d1.0-s901-t300.json').write_text(json.dumps(row))
    with pytest.raises(ValueError,match='Cached trial'):
        research.trial('candidate',901,300,1.0,checkpoint,split='selection')
