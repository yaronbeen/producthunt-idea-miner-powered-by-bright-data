# Product Hunt Idea Miner | Powered by Bright Data

> **Do not build the loudest idea. Build the one with receipts.**

Mine visible Product Hunt review excerpts for recurring complaints, feature requests, pricing objections, and switching mentions. Then turn the strongest evidence into a few falsifiable product hypotheses. Not a demand forecast. A smarter next interview.

## The decision

**Which product gap deserves a cheap validation step?**

Use it to:

- Find repeated improvement language across products you deliberately select.
- Collect exact evidence for positioning workshops and product discovery.
- Turn a vague product idea into a question that can prove it wrong.

You get **up to three** hypotheses when the evidence supports them. If it does not, you get an honest evidence gap.

## Why Bright Data

Product Hunt research dies in the copy-paste phase. [Bright Data](https://brightdata.com/) MCP lets your agent search and collect public pages as Markdown inside the same workflow that builds the evidence table. A slow or unavailable page becomes an explicit failure, not a silent hole in your analysis. That is the value: a cleaner path from public review to cited decision.

## Start with 5,000 free credits

**New Bright Data accounts include 5,000 free credits per month. No credit card is required.** Credits share one account-level pool, reset monthly, and are subject to current eligibility and product terms.

The default plan uses **up to 9 search/page requests**, plus at most **3 retries**. Your agent prints the plan before collecting. Retrieval is bounded and not guaranteed.

## What you get

- `report.md`: cue counts, evidence scope, and sample caveats.
- `reviews.csv`: stable `review_key` values, short excerpts, source URLs, and tags.
- `run.json`: a snapshot for comparing captured review content. Source IDs support edit detection; text fallback cannot distinguish an edit from a new review.
- Cross-product themes only when at least two selected products contain the same cue.

## Give this to your agent

```text
Use producthunt-idea-miner for [product category or problem].
These are my selected public Product Hunt product or review URLs: [URLs].
My product is [optional product and positioning].

Use Bright Data MCP. You may use one search for discovery and fetch at most
8 public product/review pages. Read at most 20 visible reviews per product.
Show the 9-request plan first. Retry failures at most once, with 3 retries total.
Do not claim to enumerate a category or load every review. Respect Product Hunt
terms and stop on access challenges.

Strip reviewer identities. Normalize visible excerpts and run scripts/report.py.
Return up to three falsifiable idea hypotheses only where evidence supports them.
Include disconfirming evidence and one validation question per hypothesis.
Do not estimate demand or contact reviewers.
```

## Install

Requires Python 3.10+, an agent with Bright Data MCP connected as `brightdata`, and access to this private repo.

```bash
git clone git@github.com:yaronbeen/producthunt-idea-miner-powered-by-bright-data.git \
  ~/.claude/skills/producthunt-idea-miner
```

For OpenCode, clone into `~/.config/opencode/skills/producthunt-idea-miner`. See the [connection and schema guide](docs/technical-guide.md).

## Run the example

```bash
cd ~/.claude/skills/producthunt-idea-miner
python3 scripts/report.py examples/input.json --output-dir examples/output
```

For a later run:

```bash
python3 scripts/report.py new-input.json \
  --previous examples/output/run.json --output-dir output
```

The example is synthetic. The [live-check note](docs/live-check.md) separates successful retrieval from timeouts.

## Example output

| Cue | Sample count | Products | Evidence scope |
|---|---:|---:|---|
| complaint | 1 | 1 | single_product_signal |
| feature_request | 2 | 2 | cross_product |
| pricing_objection | 1 | 1 | single_product_signal |
| switching_mention | 1 | 1 | single_product_signal |

**Good next step:** “Ask five target users whether inconsistent exports block their weekly reporting.”

**Bad next step:** “Two mentions prove a million-dollar market.” This skill refuses the second one.

## Tests

The tests came before the helper. A sanitized live excerpt later exposed a missing `I’d like` cue; the regression test now covers it.

```bash
python3 -m unittest discover -s tests -v
```

Coverage includes multi-label cues, Unicode apostrophes, dedupe, identity removal, cross-product gates, CSV injection, deterministic diffs, and sanitized live review excerpts. See [the testing note](docs/testing.md).

## What this is not

- Not a complete Product Hunt category scrape. You choose a bounded product set.
- Not a sentiment model. It is a documented cue tagger with visible limits.
- Not proof of demand, willingness to pay, or product-market fit.
- Not a reviewer prospecting tool. Identities are removed and never contacted.
- Not permission to ignore Product Hunt's current terms. Review them before collection.

## Repo map

```text
SKILL.md                 Agent workflow and MCP limits
scripts/report.py        Stdlib-only deterministic helper
tests/                   Unit tests + sanitized live fixture
examples/                Synthetic input and generated output
docs/                    Setup, schema, testing, and live-check notes
```

## FAQ

**Why supply product URLs?**  Deliberate inputs beat pretending a topic page enumerated an entire market. One optional search can help discovery; the selected URLs define the sample.

**How does the repeat-run diff work without review IDs?**  The helper hashes normalized review text within the product and source. Inserting a new review does not relabel every later row. However, an edited excerpt gets a new text key and the old key disappears; only stable source IDs support true edit detection. Rows that vanish are not labeled as removed.

**Can it write positioning?**  It gives your agent evidence and validation questions. Any final positioning remains a human decision.

---

Built by Yaron Been. MIT licensed. Powered by Bright Data, without implying endorsement.
