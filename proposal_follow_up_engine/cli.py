"""Local file CLI. No network access or external services."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from .core import SchemaError, monitor, validate
from .fixtures import dataset, expectations
from .report import render, json_text, banner

class InputError(ValueError):
    pass

class WriteError(ValueError):
    pass

def atomic_write(path, text):
    path = Path(path)
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(text)
        os.replace(temporary, path)
    except OSError as exc:
        raise WriteError(f"ReportWriteError: {path}: {exc.strerror}") from exc
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()

def read_json(path):
    def pairs(items):
        obj = {}
        for k,v in items:
            if k in obj:
                raise ValueError(f"duplicate JSON key {k}")
            obj[k] = v
        return obj
    try:
        text = path.read_text(encoding="utf-8-sig")
        return json.loads(text, object_pairs_hook=pairs)
    except json.JSONDecodeError as exc:
        raise InputError(f"ParseError: {path}: line {exc.lineno}: {exc.msg}") from exc
    except (UnicodeError, ValueError) as exc:
        raise InputError(f"ParseError: {path}: line 1: {exc}") from exc
    except OSError as exc:
        raise InputError(f"InputError: {path}: {exc.strerror}") from exc

def load_input(directory):
    directory = Path(directory)
    if not directory.is_dir():
        raise InputError(f"MissingInputError: {directory}: use --input with an existing directory; try pfue fixtures --out demo")
    files = sorted(set(directory.glob("*.proposals.json")) | set(directory.glob("input.json")))
    unsupported = [p for p in directory.iterdir() if p.suffix.lower() in (".csv", ".yaml", ".yml", ".jsonl") or (p.suffix.lower() == ".json" and p not in files and p.name != "expectations.json")]
    if unsupported:
        raise InputError(f"SchemaError: {sorted(unsupported)[0]}: line 1: unsupported input file; use input.json or *.proposals.json")
    combined = {"schema_version": 1, "synthetic": False, "entered_by": "empty snapshot", "as_of": "2026-09-30", "currency": "GBP", "proposals": []}
    sources = []
    for i,path in enumerate(files):
        data = read_json(path)
        try:
            validate(data)
            if i and any(data[k] != combined[k] for k in ("as_of", "currency")):
                raise SchemaError("field as_of/currency: all files must share snapshot date and currency")
        except SchemaError as exc:
            raise InputError(f"SchemaError: {path}: line 1 (document validation): {exc}") from exc
        if i == 0:
            combined = {**data, "proposals": []}
        combined["proposals"].extend(data["proposals"])
        sources.append({"file": path.name, "synthetic": data["synthetic"], "entered_by": data["entered_by"]})
    try:
        return monitor(combined, sources)
    except SchemaError as exc:
        raise InputError(f"SchemaError: {directory}: line 1 (combined documents): {exc}") from exc

def parser():
    p = argparse.ArgumentParser(prog="pfue", description="Compute proposal follow-up queues from explicit local inputs. No predicted savings.")
    sub = p.add_subparsers(dest="command", required=True)
    f = sub.add_parser("fixtures", help="Generate labelled synthetic ground truth", epilog="Example: pfue fixtures --out demo")
    f.add_argument("--out", required=True)
    r = sub.add_parser("run", help="Validate inputs and save computed results", epilog="Example: pfue run --input demo")
    r.add_argument("--input", required=True)
    r.add_argument("--state", default=".pfue/result.json")
    report = sub.add_parser("report", help="Render saved results with provenance", epilog="Example: pfue report --format md")
    report.add_argument("--format", choices=("md", "json"), default="md")
    report.add_argument("--state", default=".pfue/result.json")
    report.add_argument("--out")
    for name, description in (("due", "Show sent proposals due today or overdue"), ("outstanding", "Show all sent proposals and their face values")):
        cmd = sub.add_parser(name, help=description, description=description, epilog=f"Example: pfue {name} --input demo")
        cmd.add_argument("--input", required=True)
    return p

def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "fixtures":
            out = Path(args.out)
            atomic_write(out / "input.json", json_text(dataset()))
            atomic_write(out / "expectations.json", json_text(expectations()))
            atomic_write(out / "SYNTHETIC.md", "<!-- SYNTHETIC fixture header -->\n# SYNTHETIC fixture set\nAll records and expectations are synthetic. No random seed: generation uses fixed enumeration.\n")
            print("SYNTHETIC: generated 200 proposals and hand-computed expectations.")
        elif args.command == "run":
            result = load_input(args.input)
            atomic_write(args.state, json_text(result))
            print(render(result, "md"), end="")
        elif args.command == "report":
            result = read_json(Path(args.state))
            try:
                text = render(result, args.format)
            except (KeyError, TypeError, AttributeError) as exc:
                raise InputError(f"SchemaError: {args.state}: line 1: invalid result fields; rerun pfue run") from exc
            if args.out:
                atomic_write(args.out, text)
            else:
                print(text, end="")
        else:
            result = load_input(args.input)
            selected = result["ids"]["outstanding"] if args.command == "outstanding" else sorted(result["ids"]["overdue"] + result["ids"]["due_today"])
            print(json_text({"banner": banner(result), "as_of": result["as_of"], "currency": result["currency"], "honesty": result["honesty"], "proposals": [p for p in result["proposals"] if p["id"] in selected]}), end="")
        return 0
    except (InputError, WriteError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"InputError: {exc.filename}: {exc.strerror}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
