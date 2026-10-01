"""Deterministic report rendering with explicit provenance and no estimated benefits."""
import json

def json_text(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"

def banner(result):
    sources = result["provenance"]
    if not sources:
        return "DATA PROVENANCE: No proposal input files; empty snapshot."
    return "DATA PROVENANCE: " + "; ".join(
        s["file"] + (" = SYNTHETIC fixture" if s["synthetic"] else " = REAL input, declared entered by " + s["entered_by"] + " (not independently verified)")
        for s in sources)

def render(result, format="md"):
    if format == "json":
        return json_text({"banner": banner(result), **result})
    lines = ["# Proposal Follow-Up Engine", "", banner(result), "", f"Snapshot: {result['as_of']}. Currency: {result['currency']}. Amounts in integer minor units.", "", result["honesty"], "", "| Metric | Computed value |", "| --- | ---: |"]
    lines += [f"| {k} | {v} |" for k,v in sorted(result["metrics"].items())]
    lines += ["", "## Traceable proposal IDs", ""]
    lines += [f"- {k}: {', '.join(v) or '(none)'}" for k,v in sorted(result["ids"].items())]
    return "\n".join(lines) + "\n"
