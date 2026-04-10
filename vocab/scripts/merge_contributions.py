#!/usr/bin/env python3
"""
merge_contributions.py — Merge vocabulary contribution exports into the canonical data file.

Run by the maintainer after receiving contribution exports from contributors.
Adds new entries, flags conflicts for human review — nothing is auto-overwritten.

Usage:
    python scripts/merge_contributions.py \\
        --canonical data/ \\
        --contributions contrib/adam/ contrib/maria/ \\
        --output data/ \\
        --report merge_report.md
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def load_json(path: Path, default=None):
    if not path.exists():
        return default if default is not None else []
    return json.loads(path.read_text(encoding="utf-8"))


def load_manifest(contrib_dir: Path) -> dict | None:
    manifest_path = contrib_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"  Warning: no manifest.json in {contrib_dir} — skipping", file=sys.stderr)
        return None
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def merge_vocabulary(canonical: list[dict], contribution: list[dict],
                     contributor: str) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Returns (merged_canonical, new_entries, conflicts).
    conflicts: list of dicts describing each conflict for the report.
    """
    by_term = {e["term"].lower(): e for e in canonical}
    new_entries = []
    conflicts = []

    for entry in contribution:
        term = entry.get("term", "").strip()
        if not term:
            continue

        key = term.lower()
        if key not in by_term:
            enriched = dict(entry)
            if "contributor" not in enriched:
                enriched["contributor"] = contributor
            canonical.append(enriched)
            by_term[key] = enriched
            new_entries.append(enriched)
        else:
            existing = by_term[key]
            if existing.get("meaning") == entry.get("meaning"):
                continue
            conflicts.append({
                "type": "vocabulary",
                "term": term,
                "canonical": existing,
                "contribution": dict(entry),
                "contributor": contributor,
                "recommendation": (
                    "Replace — contribution is higher authority"
                    if entry.get("authority_level", 4) < existing.get("authority_level", 4)
                    else "Keep canonical — same or lower authority"
                ),
            })

    return canonical, new_entries, conflicts


def write_report(report_path: Path, contributions_processed: list[dict],
                 all_new_vocab: list[dict], all_conflicts: list[dict]) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        f"# Vocabulary Merge Report — {today}",
        "",
        "## Summary",
        f"- Contributions merged: {len(contributions_processed)} "
        f"({', '.join(c['contributor'] for c in contributions_processed)})",
        f"- New vocabulary entries added: {len(all_new_vocab)}",
        f"- Conflicts requiring review: {len(all_conflicts)}",
        "",
    ]

    if all_new_vocab:
        lines += ["## New Entries Added", "", "### Vocabulary"]
        for e in all_new_vocab:
            level = e.get("authority_level", "?")
            contrib = e.get("contributor", "unknown")
            lines.append(f"- {e['term']} ({contrib}, Level {level})")
        lines.append("")

    if all_conflicts:
        lines += ["## Conflicts Requiring Review", ""]
        for conflict in all_conflicts:
            term = conflict["term"]
            canonical = conflict["canonical"]
            contribution = conflict["contribution"]
            contributor = conflict["contributor"]
            recommendation = conflict["recommendation"]

            lines += [
                f'### vocabulary: "{term}"',
                f'**Canonical:** {canonical.get("meaning", "?")} '
                f'(Level {canonical.get("authority_level", "?")}, {canonical.get("source", "?")})',
                f'**Contribution from {contributor}:** {contribution.get("meaning", "?")} '
                f'(Level {contribution.get("authority_level", "?")}, {contribution.get("source", "?")})',
                f"**Recommendation:** {recommendation}",
                "**Action:** [ ] Accept contribution  [ ] Keep canonical  [ ] Edit",
                "",
            ]

    lines += [
        "## Next steps",
        "Review any conflicts above, then commit data/ to the repository.",
        "",
        "Update PROVENANCE.md with new contributor names and entry counts.",
    ]

    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge vocabulary contribution exports into canonical vocabulary.json"
    )
    parser.add_argument("--canonical", default="data/", metavar="DIR",
                        help="Directory containing vocabulary.json (default: data/)")
    parser.add_argument("--contributions", nargs="+", required=True, metavar="DIR",
                        help="One or more directories containing contribution exports "
                             "(each must contain manifest.json and contrib_vocabulary.json)")
    parser.add_argument("--output", default="data/", metavar="DIR",
                        help="Directory to write merged vocabulary.json (default: data/)")
    parser.add_argument("--report", default="merge_report.md", metavar="FILE",
                        help="Path to write the merge report (default: merge_report.md)")
    args = parser.parse_args()

    canonical_dir = Path(args.canonical)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    canonical_vocab = load_json(canonical_dir / "vocabulary.json", [])

    print(f"Canonical state: {len(canonical_vocab)} vocabulary entries")
    print()

    all_new_vocab: list[dict] = []
    all_conflicts: list[dict] = []
    contributions_processed: list[dict] = []

    for contrib_path_str in args.contributions:
        contrib_dir = Path(contrib_path_str)
        manifest = load_manifest(contrib_dir)
        if manifest is None:
            continue

        contributor = manifest.get("contributor", contrib_dir.name)
        print(f"Processing contribution from '{contributor}' ({contrib_dir})")

        contrib_vocab = load_json(contrib_dir / "contrib_vocabulary.json", [])

        canonical_vocab, new_vocab, vocab_conflicts = merge_vocabulary(
            canonical_vocab, contrib_vocab, contributor
        )

        all_new_vocab.extend(new_vocab)
        all_conflicts.extend(vocab_conflicts)
        contributions_processed.append(manifest)

        print(f"  Added: {len(new_vocab)} vocabulary entries")
        if vocab_conflicts:
            print(f"  Conflicts: {len(vocab_conflicts)} vocabulary")
        print()

    (output_dir / "vocabulary.json").write_text(
        json.dumps(canonical_vocab, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    report_path = Path(args.report)
    write_report(report_path, contributions_processed, all_new_vocab, all_conflicts)

    print(f"Merged vocabulary.json written to: {output_dir.resolve()}")
    print(f"Merge report written to: {report_path.resolve()}")
    print()
    print("Summary:")
    print(f"  New vocabulary entries: {len(all_new_vocab)}")
    print(f"  Conflicts to review:    {len(all_conflicts)}")

    if all_conflicts:
        print()
        print(f"Review conflicts in {report_path} before committing data/ to the repository.")


if __name__ == "__main__":
    main()
