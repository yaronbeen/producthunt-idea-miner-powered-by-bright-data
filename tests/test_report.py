import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from report import analyze, build_themes, csv_cell, normalize_reviews, tag_review, write_outputs


class ProductHuntTests(unittest.TestCase):
    def test_cues_are_multilabel_and_unclear_is_honest(self):
        self.assertEqual(set(tag_review("Please add exports. The current price is too high.")), {"feature_request", "pricing_objection"})
        self.assertIn("complaint", tag_review("The sync is broken and unreliable."))
        self.assertIn("switching_mention", tag_review("I switched from Acme to try this."))
        self.assertEqual(tag_review("Looks nice."), ["unclear"])

    def test_dedupe_and_identity_stripping(self):
        rows = [
            {"product": "Acme", "product_slug": "acme", "review_id": "r1", "text": "Please add exports.", "author": "Person", "source_url": "https://www.producthunt.com/products/acme/reviews", "captured_at": "2026-11-09"},
            {"product": "Acme", "product_slug": "acme", "review_id": "r1", "text": "Duplicate replaced", "author_handle": "person", "source_url": "https://www.producthunt.com/products/acme/reviews", "captured_at": "2026-11-09"},
        ]
        clean = normalize_reviews(rows)
        self.assertEqual(len(clean), 1)
        self.assertEqual(clean[0]["text"], "Duplicate replaced")
        self.assertNotIn("person", json.dumps(clean).lower())

    def test_cross_product_theme_requires_two_products(self):
        reviews = normalize_reviews([
            {"product": "Acme", "product_slug": "acme", "review_id": "1", "text": "Please add exports.", "source_url": "https://www.producthunt.com/products/acme/reviews", "captured_at": "2026-11-09"},
            {"product": "Beta", "product_slug": "beta", "review_id": "2", "text": "I wish it had exports.", "source_url": "https://www.producthunt.com/products/beta/reviews", "captured_at": "2026-11-09"},
        ])
        themes = build_themes(reviews)
        self.assertEqual(themes[0]["cue"], "feature_request")
        self.assertEqual(themes[0]["scope"], "cross_product")
        self.assertEqual(themes[0]["product_count"], 2)
        single = build_themes(reviews[:1])
        self.assertEqual(single[0]["scope"], "single_product_signal")

    def test_csv_safety_and_new_review_diff(self):
        self.assertEqual(csv_cell("-2+3"), "'-2+3")
        payload = {"rows": [{"product": "Acme", "product_slug": "acme", "review_id": "1", "text": "Please add exports.", "source_url": "https://www.producthunt.com/products/acme/reviews", "captured_at": "2026-11-09"}]}
        first = analyze(payload)
        changed = {"rows": payload["rows"] + [{"product": "Beta", "product_slug": "beta", "review_id": "2", "text": "The sync is broken.", "source_url": "https://www.producthunt.com/products/beta/reviews", "captured_at": "2026-11-10"}]}
        second = analyze(changed, first["snapshot"])
        statuses = {r["review_key"]: r["status"] for r in second["rows"]}
        self.assertEqual(statuses["beta:2"], "new")
        self.assertEqual(statuses["acme:1"], "unchanged")
        with tempfile.TemporaryDirectory() as tmp:
            write_outputs(second, tmp)
            self.assertIn("sample", (Path(tmp) / "report.md").read_text().lower())
            self.assertTrue((Path(tmp) / "run.json").is_file())


if __name__ == "__main__":
    unittest.main()
