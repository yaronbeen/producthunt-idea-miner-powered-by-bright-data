# Testing Product Hunt Idea Miner | Powered by Bright Data

## Test-first history

The initial commit is `test: define expected behavior (red)`. At that point the test suite failed because `scripts/report.py` did not exist. The implementation followed those tests. Later regression tests were also run before the behavior they define.

The implementation commit includes the green helper, documentation, examples, and CI. Review the git history to inspect the sequence.

## Run locally

```bash
python3 -m unittest discover -s tests -v
python3 scripts/report.py examples/input.json --output-dir /tmp/skill-example
```

No API token or network access is needed. The suite uses Python's standard-library `unittest`; there are no packages to install.

## What is covered

multi-label cues, live Unicode excerpts, source/position identity, cross-product gates, and review diffs. Shared checks also cover CSV formula-injection protection, deterministic output, and generated report/snapshot files.

`tests/fixtures/sanitized_live.json` contains a small sanitized observation from the documented MCP smoke check where source evidence was available. Synthetic examples remain clearly labeled and never masquerade as live source data.

## What is not covered

Unit tests do not guarantee that a third-party page will remain available, that its markup will stay unchanged, or that a source permits every use. The agent workflow handles live failures explicitly. Review `docs/live-check.md` for the observed behavior and its limits.
