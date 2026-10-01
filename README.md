# Proposal Follow-Up Engine

`pfue` monitors outstanding proposals from local JSON snapshots. It computes follow-up queues; it never contacts clients, discovers facts, predicts outcomes, or estimates benefits. CPU only, Python standard library runtime, no network calls, no language models.

Hypothesis: explicit inputs, deterministic computation, planted ground truth, and named errors make a trustworthy proposal monitoring CLI for Henry's outreach operation.

## Quickstart

Python 3.10 or newer and setuptools 68 or newer are required for installation. From the repository, install using already available local packaging tools:

```powershell
python -m pip install --no-index --no-deps --no-build-isolation -e .
$env:Path += ";" + (python -c "import sysconfig; print(sysconfig.get_path('scripts', scheme='nt_user'))")
pfue fixtures --out demo
pfue run --input demo
pfue report --format md
pfue due --input demo
```

Without installation, use `python -m proposal_follow_up_engine.cli` in place of `pfue`. For tests, use an already installed pytest: `python -m pytest -q`. No dependency downloads are needed. The hand-written five-record starting example is `examples/synthetic-five/input.json`; run it with `pfue run --input examples/synthetic-five`. Default state is `.pfue/result.json`, relative to the current working directory. `run` replaces this state only after successful validation. After a failed run, any previous state remains the previous snapshot; rerun successfully before reporting.

## Input format reference

An input directory contains `input.json` and/or `*.proposals.json`. These are UTF-8 JSON documents. `expectations.json` is fixture metadata and never input. Markdown labels are ignored. Other JSON names, CSV, YAML, and JSONL are rejected with a named schema error; this version supports JSON only. An empty directory is a valid zero snapshot with explicit default date 2026-09-30 and currency GBP.

```json
{
  "schema_version": 1,
  "synthetic": false,
  "entered_by": "Henry",
  "as_of": "2026-09-30",
  "currency": "GBP",
  "proposals": [
    {
      "id": "proposal-001",
      "client": "Example client (illustrative, replace before real use)",
      "amount_minor": 10000,
      "status": "sent",
      "sent_on": "2026-09-01",
      "follow_up_on": "2026-10-01"
    }
  ]
}
```

The example above is illustrative schema documentation, not real data or a measured business result. When copying it for practice, set `synthetic` to `true`. Henry enters his own real data by hand and declares `synthetic: false` and `entered_by: Henry`. The tool cannot independently verify this declaration. Do not commit real data or trial results.

All displayed object fields are required; unknown fields are schema errors. `schema_version` is integer 1. `synthetic` is a boolean. `entered_by` is nonempty text, maximum 200 characters. All files must share `as_of` and `currency` (GBP, USD, EUR); mixed currencies are never summed. Dates must be canonical YYYY-MM-DD. `as_of` is the supplied analysis date, never the wall clock. Future sent dates relative to `as_of` are rejected; future follow-up dates are valid upcoming work. Follow-up dates before sent dates are rejected.

IDs are nonempty text up to 200 characters, unique across every file. Client names are nonempty text up to 10,000 characters. Unicode and Windows paths are supported as text (escape backslashes in JSON). Control characters and em dash characters are rejected. Strings beyond limits are named errors, never truncated. Amounts are integers from 0 to 1,000,000,000,000 in currency minor units; booleans, decimals, negatives, and larger values are rejected. No rounding or float arithmetic occurs.

Statuses: `sent` is outstanding; `accepted`, `declined`, and `withdrawn` are closed. A sent proposal is overdue when follow-up date is before `as_of`, due today on equality, otherwise upcoming. There is no inferred expiry, follow-up cadence, or likelihood of winning. Closed proposals never enter follow-up queues. Total count equals closed plus outstanding; outstanding equals overdue plus due today plus upcoming, both for counts and face values. Reports include IDs and JSON includes every original proposal so sums can be checked.

## Subcommands

| Command | Purpose and example |
| --- | --- |
| fixtures | Generate 200 synthetic records: `pfue fixtures --out demo` |
| run | Validate and compute: `pfue run --input demo --state .pfue/result.json` |
| report | Render saved results: `pfue report --format json --out report.json` |
| due | Show overdue and due-today proposals with provenance: `pfue due --input demo` |
| outstanding | Show all sent proposals with provenance: `pfue outstanding --input demo` |

Every command has `--help`. Reports support `md` and `json`; use `--state` to choose a saved snapshot. Due and outstanding compute directly from inputs. No commands send messages or modify proposals. Success exits 0, named runtime errors exit 2. Files are written through temporary siblings and atomic replacement; failed writes leave no partial target. Existing targets are replaced on success. Parse errors name file and JSON line. Schema errors identify the offending field and document start line 1; this is not a claim of an exact field source line. Missing inputs include a usage hint. Malformed CSV/YAML is rejected as unsupported rather than parsed.

## Architecture

```text
local JSON --> CLI loader + schema validation --> pure core monitor
                                                     |
                                                     v
                                              saved JSON snapshot
                                                     |
                                                     v
                                        provenance + MD/JSON report
fixture generator --> labelled records + independent expectations
pytest --> ground truth, adversarial, error, and deterministic checks
```

## Honesty boundary and fixture policy

Every figure is computed from supplied input. Face values are not revenue or money saved. Time and money savings are unmeasured and therefore not reported. No hypothetical savings fields are available. Input provenance is visible in run, report, due, and outstanding outputs: each filename is labelled SYNTHETIC or REAL with declared author, with real provenance explicitly unverified. The real path uses Henry's manually entered data; no real trial results ship here.

Every synthetic JSON file carries `synthetic: true` (JSON cannot carry header comments). Each fixture directory includes a Markdown header comment labelling it SYNTHETIC. The expectations file is explicitly labelled synthetic. The five-record example follows the same policy. Generation has no randomness and no seed: fixed enumeration, fixed dates, sorted outputs, integer arithmetic, UTF-8 and LF. Same inputs produce byte-identical outputs; runtime measurement is kept in evidence, not deterministic reports.

The 200-record fixture has 40 blocks of five, each with three sent, one accepted and one declined proposal. Each face value is 10,000 minor units. Hand arithmetic: 200 total, 80 closed, 120 outstanding; 40 each overdue, due today and upcoming. Outstanding face value is 1,200,000 minor units; each queue totals 400,000. Tests assert the exact ID sets, not just counts, and change a planted record to prove the report is computed.

## Acceptance evidence and limitations

See `EVIDENCE.md` for local test and timed demo measurements. Acceptance requires the full demo below five seconds, exact figures and zero false positives on synthetic planted ground truth. Synthetic accuracy does not establish real-world accuracy or commercial demand. Incorrect entered statuses or dates produce incorrect queues; clients changing their minds are invisible until inputs are updated. Duplicate IDs, schema drift and parse errors block the whole run rather than dropping rows. Saved state does not automatically refresh. Multi-file processing is a snapshot, not transaction history. A completed proposal with a past follow-up date remains closed.

## Evidence-based improvement hook and verdict

The primary real-use metric is queue classification error rate on a hand-checked sample: incorrect due/outstanding classification divided by sampled proposals. Start a two-week window when Henry begins real use. Record start/end dates, actual usage days, sample selection, sample size, discrepancies, and numerator/denominator in a private local trial log. Check at least 20 proposals spanning closed, overdue, today, and upcoming if available; record a smaller sample honestly. An empty sample means unmeasured, never zero error.

After two weeks, if error exceeds 10 percent, fix the largest evidenced failure cause and repeat the check, or kill with a recorded reason. If the tool is unused, record that and kill. Only report time saved after measuring a comparable baseline and tool runs; none has been measured here. One evidence-based build improvement already made: exact-set checks and corrupted-record testing verify computed classification rather than totals alone, addressing the possibility that matching aggregate counts hide wrong recipients.

Verdict is pending the two-week real-use window, with no invented demand evidence. At that review, record one of: expand for daily use or revenue; integrate for heavy sibling overlap; commercialise if a buyer will pay as-is; maintain for portfolio evidence when acceptance is met but stronger demand is absent; kill if never used or acceptance cannot be met. See `VERDICT.md` for the record template.
