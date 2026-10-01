import json
from proposal_follow_up_engine.cli import main
from proposal_follow_up_engine.fixtures import dataset

def test_fixtures_labelled_synthetic(tmp_path):
    assert main(["fixtures", "--out", str(tmp_path)])==0
    for path in tmp_path.glob("*.json"):
        assert json.loads(path.read_text(encoding="utf-8"))["synthetic"] is True
    assert tmp_path.joinpath("SYNTHETIC.md").read_text().startswith("<!-- SYNTHETIC")
    assert len(dataset()["proposals"])==200
