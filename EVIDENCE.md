# Local acceptance evidence

Measured on 2026-10-01 with Python 3.12.10 on Windows, CPU only.

Test command: `python -m pytest -q`.
Result: .......................................                                  [100%]
39 passed in 0.44s

Installed CLI demo, timed with `time.perf_counter` around all three separate processes including startup and captured report rendering:

```text
pfue fixtures --out demo
pfue run --input demo
pfue report --format md
```

Measured elapsed: 0.806596 seconds. Acceptance threshold: below 5 seconds. This measures local synthetic demo runtime, not time saved against a baseline. Report output was rendered successfully with a SYNTHETIC provenance banner. Ground-truth assertions cover all 200 records, exact classification ID sets and integer totals. There are zero false positives and zero missing planted cases in those asserted synthetic sets.

The hand-written five-record example is also checked. Corruption evidence: closing P001 reduces overdue count from 40 to 39 and overdue face value from 400000 to 390000 minor units. Identical repeated fixtures, state and reports are checked byte-for-byte. Error tests exercise malformed input, schema drift, duplicate IDs, missing directories, mixed currencies and write failure without a partial target.

Scope: local synthetic acceptance only. Real-use accuracy, adoption, revenue and savings remain unmeasured. No network or GPU workload was used. Publishing is deferred to the separate verification step.
