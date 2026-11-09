# Product Hunt Live Check | Powered by Bright Data

Checked 2026-11-09 with Bright Data MCP `scrape_as_markdown`.

## What worked

`https://www.producthunt.com/products/chatgpt/reviews` returned public Markdown with the product summary and visible review sections. The page displayed 762 reviews, but the skill treats that as a page label, not as the number collected.

Two short excerpts were sanitized into `tests/fixtures/sanitized_live.json`. Names, handles, avatars, ratings, and unrelated content were removed. One excerpt began with a curly-apostrophe form of `I’d like`; it exposed a missing feature-request cue. The new test failed before the tagger was fixed.

## What failed or remains limited

- A topic page timed out during early validation.
- The ChatGPT reviews URL timed out on one later attempt and succeeded on the bounded retry.
- The capture is not category enumeration and does not promise access to every review.
- Visible reviews may have no stable per-review ID. The skill supports position fallback and discloses its weakness.

Review Product Hunt's current terms before collection. The skill stops on access challenges and never describes MCP as a way around them.
