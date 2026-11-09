# Testing Product Hunt Idea Miner | Powered by Bright Data

## Test-first history

The initial commit is `test: define expected behavior (red)`. At that point the suite failed because `scripts/report.py` did not exist. The implementation followed. Review regression cases have a separate `test: add review regression cases (red)` commit before their fix commit.

The usability additions have a separate `test: define usability upgrades (red)` commit before their implementation. The history also includes documentation and generated examples. Not every later assertion was individually proven red; the git sequence shows the initial, review, and usability rounds rather than claiming a separate commit for every assertion.

## Run locally

```bash
python3 -m unittest discover -s tests -v
python3 scripts/report.py examples/input.json --output-dir /tmp/skill-example
```

No API token or network access is needed. The suite uses Python's standard-library `unittest`; there are no packages to install.

## What is covered

multi-label cues, negated praise, live Unicode excerpts, source/text identity, insertion-safe diffs, cross-product gates, and validation evidence packets. Shared checks also cover MCP installation documentation, CSV formula-injection protection, deterministic output, and generated report/snapshot files.

`tests/fixtures/sanitized_live.json` contains a small sanitized observation from the documented MCP smoke check where source evidence was available. Synthetic examples remain clearly labeled and never masquerade as live source data.

## What is not covered

Unit tests do not guarantee that a third-party page will remain available, that its markup will stay unchanged, or that a source permits every use. The agent workflow handles live failures explicitly. Review `docs/live-check.md` for the observed behavior and its limits.
