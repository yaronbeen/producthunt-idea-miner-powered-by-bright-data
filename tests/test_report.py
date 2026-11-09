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
            {"product": "Acme", "product_slug": "acme", "review_id": "r1", "text": "Please add exports.", "author": "Person", "owner": "Owner", "profile_url": "https://example.com/person", "user_name": "person", "linkedin": "https://linkedin.com/in/person", "contact": "person@example.com", "source_url": "https://www.producthunt.com/products/acme/reviews", "captured_at": "2026-11-09"},
            {"product": "Acme", "product_slug": "acme", "review_id": "r1", "text": "Duplicate replaced", "author_handle": "person", "source_url": "https://www.producthunt.com/products/acme/reviews", "captured_at": "2026-11-09"},
        ]
        clean = normalize_reviews(rows)
        self.assertEqual(len(clean), 1)
        self.assertEqual(clean[0]["text"], "Duplicate replaced")
        self.assertNotIn("person", json.dumps(clean).lower())
        self.assertNotIn("owner", json.dumps(clean).lower())
        self.assertNotIn("profile_url", json.dumps(clean).lower())
        self.assertNotIn("linkedin", json.dumps(clean).lower())
        self.assertNotIn("contact", json.dumps(clean).lower())

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

    def test_text_fallback_does_not_shift_when_a_review_is_inserted(self):
        first_rows = [
            {"product": "Acme", "product_slug": "acme", "position": 1, "text": "Please add exports.", "source_url": "https://www.producthunt.com/products/acme/reviews", "captured_at": "2026-11-09"},
            {"product": "Acme", "product_slug": "acme", "position": 2, "text": "The sync is broken.", "source_url": "https://www.producthunt.com/products/acme/reviews", "captured_at": "2026-11-09"},
        ]
        first = analyze({"rows": first_rows})
        inserted = {"product": "Acme", "product_slug": "acme", "position": 1, "text": "I wish it had an API.", "source_url": "https://www.producthunt.com/products/acme/reviews", "captured_at": "2026-11-10"}
        shifted = [dict(first_rows[0], position=2, captured_at="2026-11-10"), dict(first_rows[1], position=3, captured_at="2026-11-10")]
        second = analyze({"rows": [inserted] + shifted}, first["snapshot"])
        by_text = {row["text"]: row for row in second["rows"]}
        self.assertEqual(by_text["Please add exports."]["status"], "unchanged")
        self.assertEqual(by_text["The sync is broken."]["status"], "unchanged")
        self.assertEqual(by_text["I wish it had an API."]["status"], "new")
        self.assertTrue(all(row["identity_strength"] == "text_fallback" for row in second["rows"]))

    def test_negated_praise_does_not_become_an_objection(self):
        self.assertEqual(tag_review("Nothing missing. It is cost-effective."), ["unclear"])
        self.assertEqual(tag_review("No bugs and not confusing."), ["unclear"])
        self.assertIn("pricing_objection", tag_review("The cost is too high."))
        self.assertEqual(tag_review("Great price and simple pricing."), ["unclear"])

    def test_sanitized_live_capture_cues(self):
        fixture = json.loads((Path(__file__).parent / "fixtures" / "sanitized_live.json").read_text())
        for row in fixture["rows"]:
            with self.subTest(row=row["text"]):
                self.assertEqual(tag_review(row["text"]), row["expected_tags"])


    def test_cross_product_evidence_becomes_a_validation_packet(self):
        rows = [
            {"product": "Acme", "product_slug": "acme", "review_id": "1", "text": "Please add exports.", "source_url": "https://www.producthunt.com/products/acme/reviews"},
            {"product": "Beta", "product_slug": "beta", "review_id": "2", "text": "I wish it had exports.", "source_url": "https://www.producthunt.com/products/beta/reviews"},
        ]
        result = analyze({"rows": rows})
        self.assertIn("Please add exports.", result["validation_packets"])
        self.assertIn("https://www.producthunt.com/products/acme/reviews", result["validation_packets"])
        self.assertIn("Validation question", result["validation_packets"])
        single = analyze({"rows": rows[:1]})
        self.assertIn("No cross-product evidence packets", single["validation_packets"])
        broad_rows = [dict(row, text="Please add exports. The sync is broken and expensive. I switched from Legacy.") for row in rows]
        self.assertEqual(analyze({"rows": broad_rows})["validation_packets"].count("\n## "), 3)
        with tempfile.TemporaryDirectory() as tmp:
            write_outputs(result, tmp)
            self.assertTrue((Path(tmp) / "validation-packets.md").is_file())

    def test_bright_data_mcp_installation_is_documented(self):
        root = Path(__file__).parents[1]
        readme = (root / "README.md").read_text()
        guide = (root / "docs" / "install-bright-data-mcp.md").read_text()
        self.assertNotIn("private repo", readme.lower())
        self.assertIn("docs/install-bright-data-mcp.md", readme)
        self.assertIn("@brightdata/mcp", guide)
        self.assertIn("https://mcp.brightdata.com/mcp?token=", guide)
        self.assertIn("search_engine,scrape_as_markdown", guide)
        self.assertIn("{env:BRIGHT_DATA_API_TOKEN}", guide)

    def test_shipped_example_output_and_readme_table_are_current(self):
        root = Path(__file__).parents[1]
        result = analyze(json.loads((root / "examples" / "input.json").read_text()))
        self.assertEqual(result["report"], (root / "examples" / "output" / "report.md").read_text())
        readme = (root / "README.md").read_text()
        for line in result["report"].splitlines():
            if line.startswith("|"):
                self.assertIn(line, readme)


if __name__ == "__main__":
    unittest.main()
