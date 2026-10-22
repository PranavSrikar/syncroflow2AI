from pathlib import Path
import xml.etree.ElementTree as ET
import pytest


def test_poisson_parameters_are_rates_for_documented_mean_headways():
    root=Path(__file__).resolve().parents[2]/'sumo_scenarios/two_junction'
    flows=ET.parse(root/'corridor.rou.xml').getroot().findall('flow')
    expected={'west_east':600,'east_west':450,'a_north_south':400,
              'a_south_north':300,'b_north_south':3600/7,'b_south_north':3600/11}
    assert {f.get('id') for f in flows}==set(expected)
    for flow in flows:
        value=flow.get('period')
        assert value.startswith('exp(') and value.endswith(')')
        rate=float(value[4:-1])
        assert rate*3600==pytest.approx(expected[flow.get('id')])
        assert 0<rate<.25
    legacy=ET.parse(root/'corridor.legacy-saturated.rou.xml').getroot().findall('flow')
    assert sum(float(f.get('period')[4:-1]) for f in legacy)==53
