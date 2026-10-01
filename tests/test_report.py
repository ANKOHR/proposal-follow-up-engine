import json
from proposal_follow_up_engine.core import monitor
from proposal_follow_up_engine.fixtures import dataset, expectations
from proposal_follow_up_engine.report import render

def result(synthetic=True):
    return monitor(dataset(), [{"file":"input.json", "synthetic":synthetic, "entered_by":"Henry"}])

def test_report_matches_ground_truth_exact():
    assert json.loads(render(result(), "json"))["metrics"]==expectations()["metrics"]

def test_report_zero_false_positives():
    actual=json.loads(render(result(), "json"))["ids"]
    for key, ids in expectations()["ids"].items():
        assert set(actual[key])==set(ids)

def test_report_carries_provenance_banner():
    for fmt in ("md", "json"):
        assert "DATA PROVENANCE" in render(result(),fmt)
        assert "SYNTHETIC fixture" in render(result(),fmt)
        assert "REAL input, declared entered by Henry" in render(result(False),fmt)

def test_hypothetical_figures_labelled():
    for fmt in ("md", "json"):
        text=render(result(),fmt)
        assert "unmeasured" in text and "not earned revenue" in text
        assert "money_saved" not in text

def test_no_em_dashes_in_outputs():
    for fmt in ("md", "json"):
        assert chr(0x2014) not in render(result(),fmt)

def test_determinism_byte_identical():
    for fmt in ("md", "json"):
        assert render(result(),fmt).encode()==render(result(),fmt).encode()
