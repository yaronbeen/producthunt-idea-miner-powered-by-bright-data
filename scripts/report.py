#!/usr/bin/env python3
"""Tag normalized Product Hunt review excerpts without inventing demand."""
import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

CUES = {
    "feature_request": ("please add", "wish", "would like", "i'd like", "missing", "should have", "could use", "need support for"),
    "complaint": ("broken", "unreliable", "confusing", "slow", "bug", "hate", "doesn't work", "frustrating"),
    "pricing_objection": ("expensive", "too high", "overpriced", "costly", "pricey", "not worth the price", "not affordable"),
    "switching_mention": ("switched", "switching", "migrated", "moved from", "alternative to"),
}
PUBLIC_FIELDS = {"product", "product_slug", "review_id", "position", "text", "source_url", "captured_at"}
VALIDATION_QUESTIONS = {
    "feature_request": "Tell me about the last time you needed this capability. What did you do instead, and what did that workaround cost?",
    "complaint": "Walk me through the last time this problem happened. What was the impact, and how did you recover?",
    "pricing_objection": "What do you use today, and what would make a different price or package worth choosing?",
    "switching_mention": "What triggered your last switch, what nearly stopped it, and what did migration cost?",
}


def csv_cell(value):
    text = "" if value is None else str(value)
    return "'" + text if text.startswith(("=", "+", "-", "@", "\t", "\r")) else text


def cue_present(text, phrase):
    pattern = re.compile(r"(?<![\w-])" + re.escape(phrase) + r"(?![\w-])")
    for match in pattern.finditer(text):
        prefix = text[max(0, match.start() - 40):match.start()]
        if not re.search(r"\b(?:no|not|nothing|never|without)\s+(?:[\w']+\s+){0,1}$", prefix):
            return True
    return False


def tag_review(text):
    lowered = text.lower().replace("’", "'")
    tags = [cue for cue, phrases in CUES.items() if any(cue_present(lowered, phrase) for phrase in phrases)]
    return tags or ["unclear"]


def public_record(record):
    return {k: v for k, v in record.items() if k in PUBLIC_FIELDS}


def normalize_text(text):
    return " ".join(text.lower().replace("’", "'").split())


def normalize_reviews(records):
    deduped = {}
    for raw in records:
        row = public_record(raw)
        slug = str(row.get("product_slug", "")).strip().lower()
        text = str(row.get("text", "")).strip()
        if not slug or not text:
            raise ValueError("Every review needs product_slug and text")
        if row.get("review_id"):
            review_id = str(row["review_id"])
            identity_strength = "source_id"
        else:
            basis = f"{row.get('source_url', '')}|{slug}|{normalize_text(text)}"
            review_id = "text-" + hashlib.sha256(basis.encode()).hexdigest()[:12]
            identity_strength = "text_fallback"
        row.update({"product_slug": slug, "review_id": review_id, "identity_strength": identity_strength, "review_key": f"{slug}:{review_id}", "text": text, "tags": tag_review(text)})
        deduped[row["review_key"]] = row
    return [deduped[key] for key in sorted(deduped)]


def build_themes(reviews):
    groups = defaultdict(list)
    for row in reviews:
        for cue in row["tags"]:
            if cue != "unclear":
                groups[cue].append(row)
    themes = []
    for cue, rows in groups.items():
        products = sorted({r["product_slug"] for r in rows})
        themes.append({
            "cue": cue,
            "sample_count": len(rows),
            "product_count": len(products),
            "scope": "cross_product" if len(products) >= 2 else "single_product_signal",
            "products": products,
            "evidence": [{"review_key": r["review_key"], "text": r["text"][:240], "source_url": r.get("source_url"), "captured_at": r.get("captured_at")} for r in rows[:5]],
        })
    return sorted(themes, key=lambda r: r["cue"])


def comparison_value(value):
    if isinstance(value, dict):
        return {k: comparison_value(v) for k, v in value.items() if k not in {"status", "captured_at", "position"}}
    if isinstance(value, list):
        return [comparison_value(v) for v in value]
    return value


def apply_diff(rows, previous):
    old = {r["review_key"]: comparison_value(r) for r in (previous or {}).get("rows", [])}
    for row in rows:
        identity = row["review_key"]
        row["status"] = "new" if identity not in old else ("unchanged" if old[identity] == comparison_value(row) else "changed")
    return rows


def md(value):
    return " ".join(str(value if value is not None else "").split()).replace("|", "\\|")


def render_validation_packets(themes):
    eligible = sorted((t for t in themes if t["scope"] == "cross_product"), key=lambda t: (-t["product_count"], -t["sample_count"], t["cue"]))[:3]
    lines = ["# Product Hunt validation evidence packets | Powered by Bright Data", "", "Use these excerpts to prepare interviews, not to estimate demand. A cue is a research lead, not a product requirement.", ""]
    if not eligible:
        lines.append("No cross-product evidence packets. Collect the same cue on at least two deliberately selected products before using this file for theme validation.")
        return "\n".join(lines) + "\n"
    for theme in eligible:
        lines += [f"## {md(theme['cue'])}", "", f"Observed in {theme['sample_count']} excerpts across {theme['product_count']} products in this capture.", "", "### Exact evidence", ""]
        for evidence in theme["evidence"]:
            lines.append(f"- `{md(evidence['review_key'])}`: “{md(evidence['text'])}” — {md(evidence.get('source_url') or 'source not captured')}")
        lines += ["", f"**Validation question:** {VALIDATION_QUESTIONS[theme['cue']]}", "", "**Falsifier:** If target users do not recognize the problem, already solve it cheaply, or will not change their workflow, reject or narrow the theme.", ""]
    return "\n".join(lines) + "\n"


def render(result):
    lines = ["# Product Hunt Idea Miner | Powered by Bright Data", "", f"Captured sample: {len(result['rows'])} visible review excerpts. Counts describe this sample only; they are not demand estimates.", "", "| Cue | Sample count | Products | Evidence scope |", "|---|---:|---:|---|"]
    for theme in result["themes"]:
        lines.append(f"| {theme['cue']} | {theme['sample_count']} | {theme['product_count']} | {theme['scope']} |")
    lines += ["", "Generate up to three idea hypotheses only where the evidence supports them. Every hypothesis needs a falsification question. An empty theme table is a valid result."]
    return "\n".join(lines) + "\n"


def analyze(payload, previous=None):
    rows = apply_diff(normalize_reviews(payload.get("rows", [])), previous)
    run_id = hashlib.sha256(json.dumps(comparison_value(rows), sort_keys=True).encode()).hexdigest()[:12]
    result = {"rows": rows, "themes": build_themes(rows), "snapshot": {"schema_version": 1, "run_id": run_id, "rows": rows}}
    result["report"] = render(result)
    result["validation_packets"] = render_validation_packets(result["themes"])
    return result


def write_outputs(result, output_dir):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.md").write_text(result["report"])
    (out / "run.json").write_text(json.dumps(result["snapshot"], indent=2, sort_keys=True) + "\n")
    (out / "validation-packets.md").write_text(result["validation_packets"])
    fields = ["review_key", "product", "product_slug", "text", "tags", "status", "source_url", "captured_at"]
    with (out / "reviews.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in result["rows"]:
            writer.writerow({key: csv_cell(json.dumps(row[key]) if key == "tags" else row.get(key)) for key in fields})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("--previous", help="Prior run.json; omit on the first run")
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()
    payload = json.loads(Path(args.input).read_text())
    previous = json.loads(Path(args.previous).read_text()) if args.previous else None
    write_outputs(analyze(payload, previous), args.output_dir)


if __name__ == "__main__":
    main()
