import copy
import pytest
from proposal_follow_up_engine.core import monitor, SchemaError
from proposal_follow_up_engine.fixtures import dataset, expectations

def test_fixture_ground_truth_matches_hand_computed():
    result = monitor(dataset(), [])
    assert result["metrics"] == expectations()["metrics"]
    assert result["ids"] == expectations()["ids"]

@pytest.mark.parametrize("field,value", [("amount_minor", -1), ("amount_minor", True), ("amount_minor", 1.5), ("amount_minor", 10**13), ("sent_on", "2026-10-01"), ("sent_on", "bad"), ("follow_up_on", "2026-08-01"), ("client", "x"*10001), ("status", "unknown"), ("client", chr(0x2014))])
def test_rejects_adversarial_values(field,value):
    data = dataset(); data["proposals"][0][field] = value
    with pytest.raises(SchemaError, match=field):
        monitor(data, [])

def test_duplicate_ids():
    data = dataset(); data["proposals"][1]["id"] = data["proposals"][0]["id"]
    with pytest.raises(SchemaError, match="duplicate"):
        monitor(data, [])

def test_corrupted_ground_truth_changes_computation():
    data=dataset(); data["proposals"][0]["status"]="accepted"
    result=monitor(data, [])
    assert result["metrics"]["outstanding_count"]==119
    assert result["metrics"]["overdue_amount_minor"]==390000
    assert "P001" not in result["ids"]["overdue"]

def test_handles_unicode_and_long_inputs():
    data=dataset(5); data["proposals"][0]["client"]="Zoë 東京 C:\\Users\\henry " + "é"*9000
    assert monitor(data, [])["proposals"][0]["client"]==data["proposals"][0]["client"]

def test_smallest_five_record_input():
    assert monitor(dataset(5), [])["metrics"]["outstanding_count"]==3

def test_schema_drift():
    data=dataset(); data["proposals"][0]["extra"]=1
    with pytest.raises(SchemaError, match="extra"):
        monitor(data, [])
