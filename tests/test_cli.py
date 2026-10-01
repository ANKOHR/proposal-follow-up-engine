import json
import time
import pytest
from proposal_follow_up_engine.cli import main, load_input
from proposal_follow_up_engine.fixtures import dataset
from proposal_follow_up_engine.report import json_text

def setup(tmp_path):
    main(["fixtures","--out",str(tmp_path / "input")])
    return tmp_path / "input", tmp_path / "state.json"

def test_run_completes_on_fixture(tmp_path,capsys):
    inp,state=setup(tmp_path)
    start=time.perf_counter()
    assert main(["run","--input",str(inp),"--state",str(state)])==0
    assert main(["report","--state",str(state),"--format","md"])==0
    assert time.perf_counter()-start<5
    assert "DATA PROVENANCE" in capsys.readouterr().out

def test_empty_input_renders_without_traceback(tmp_path,capsys):
    state=tmp_path/"state.json"
    assert main(["run","--input",str(tmp_path),"--state",str(state)])==0
    assert main(["report","--state",str(state)])==0
    assert json.loads(state.read_text())["metrics"]["total_count"]==0

@pytest.mark.parametrize("text", ["{broken", '{"a":1,"a":2}'])
def test_malformed_input_named_error(tmp_path,capsys,text):
    (tmp_path/"input.json").write_text(text)
    assert main(["run","--input",str(tmp_path)])==2
    err=capsys.readouterr().err
    assert "ParseError" in err and "input.json" in err and "line" in err

@pytest.mark.parametrize("command",["fixtures","run","report","due","outstanding"])
def test_cli_smoke_all_subcommands(tmp_path,command):
    inp,state=setup(tmp_path)
    main(["run","--input",str(inp),"--state",str(state)])
    args={"fixtures":["--out",str(inp)], "run":["--input",str(inp),"--state",str(state)],"report":["--state",str(state),"--format","json"],"due":["--input",str(inp)],"outstanding":["--input",str(inp)]}
    assert main([command]+args[command])==0
    with pytest.raises(SystemExit) as exc:
        main([command,"--help"])
    assert exc.value.code==0

def test_cli_determinism(tmp_path):
    inp,state=setup(tmp_path)
    args=["run","--input",str(inp),"--state",str(state)]
    main(args); first=state.read_bytes(); main(args)
    assert state.read_bytes()==first
    main(["fixtures","--out",str(inp)]); first=(inp/"input.json").read_bytes()
    main(["fixtures","--out",str(inp)])
    assert (inp/"input.json").read_bytes()==first

def test_missing_input(tmp_path,capsys):
    assert main(["run","--input",str(tmp_path/"missing")])==2
    assert "MissingInputError" in capsys.readouterr().err

def test_report_write_failure_no_partial_file(tmp_path,capsys):
    inp,state=setup(tmp_path); main(["run","--input",str(inp),"--state",str(state)])
    blocker=tmp_path/"blocker"; blocker.write_text("original")
    assert main(["report","--state",str(state),"--out",str(blocker/"report.md")])==2
    assert "ReportWriteError" in capsys.readouterr().err
    assert blocker.read_text()=="original"
    assert not list(tmp_path.glob("tmp*"))

def test_multi_file_provenance_and_duplicates(tmp_path,capsys):
    a=dataset(5); b=dataset(5); b["synthetic"]=False; b["entered_by"]="Henry"
    for p in b["proposals"]: p["id"]="real-"+p["id"]
    (tmp_path/"a.proposals.json").write_text(json_text(a),encoding="utf-8")
    (tmp_path/"b.proposals.json").write_text(json_text(b),encoding="utf-8")
    assert len(load_input(tmp_path)["provenance"])==2
    b["proposals"][0]["id"]="P001"
    (tmp_path/"b.proposals.json").write_text(json_text(b),encoding="utf-8")
    assert main(["run","--input",str(tmp_path)])==2
    assert "duplicate id" in capsys.readouterr().err


def test_hand_written_five_record_example():
    result=load_input("examples/synthetic-five")
    assert result["metrics"]["total_count"]==5
    assert result["metrics"]["closed_count"]==2
    assert result["metrics"]["outstanding_amount_minor"]==60000
    assert result["ids"]["overdue"]==["one"]
    assert result["ids"]["due_today"]==["two"]
    assert result["ids"]["upcoming"]==["three"]


def test_mismatched_currency_named_error(tmp_path,capsys):
    a=dataset(5); b=dataset(5); b["currency"]="USD"
    (tmp_path/"a.proposals.json").write_text(json_text(a))
    (tmp_path/"b.proposals.json").write_text(json_text(b))
    assert main(["run","--input",str(tmp_path)])==2
    assert "as_of/currency" in capsys.readouterr().err


def test_invalid_saved_state_named_error(tmp_path,capsys):
    state=tmp_path/"state.json"; state.write_text("{}")
    assert main(["report","--state",str(state)])==2
    assert "SchemaError" in capsys.readouterr().err
