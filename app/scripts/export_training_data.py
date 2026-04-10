#!/usr/bin/env python3
"""
Training data export script (Decision 16).

Queries interactions joined to approved feedback and writes training data
to JSONL format. Only reviewed=true, applied=true feedback is eligible.

Usage:
    python scripts/export_training_data.py \\
        --format sft \\
        --min_authority_level 2 \\
        --after 2025-01-01 \\
        --output training_sft.jsonl

    python scripts/export_training_data.py \\
        --format dpo \\
        --min_authority_level 1 \\
        --output training_dpo.jsonl

Output formats:

  SFT (supervised fine-tuning) — confirmed correct response pairs:
    thumbs_up:   {"prompt": "...", "response": "<original LLM response>"}
    thumbs_down: {"prompt": "...", "response": "<correction>"}   (correction preferred)

  DPO (preference fine-tuning) — correct vs rejected triples:
    thumbs_down with correction only:
    {"prompt": "...", "chosen": "<correction>", "rejected": "<original LLM response>"}

Authority levels:
  1 = Native speaker verified
  2 = Linguistic / academic source
  3 = Community sources
  4 = LLM inference

  --min_authority_level filters to feedback where authority_level <= N,
  i.e. level 1 means only native-speaker-verified corrections.
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path


async def run(args: argparse.Namespace) -> None:
    try:
        import asyncpg
    except ImportError:
        print("ERROR: asyncpg not installed. Run: pip install asyncpg", file=sys.stderr)
        sys.exit(1)

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print(
            "ERROR: DATABASE_URL environment variable not set.\n"
            "Example: export DATABASE_URL=postgresql://kapampangan:password@localhost:5432/kapampangan",
            file=sys.stderr,
        )
        sys.exit(1)

    conn = await asyncpg.connect(database_url)

    try:
        # Build WHERE clause
        clauses = [
            "f.reviewed = TRUE",
            "f.applied = TRUE",
            f"f.authority_level <= {args.min_authority_level}",
        ]
        params: list = []
        idx = 1

        if args.after:
            clauses.append(f"f.timestamp >= ${idx}::timestamptz")
            params.append(args.after)
            idx += 1
        if args.before:
            clauses.append(f"f.timestamp <= ${idx}::timestamptz")
            params.append(args.before)
            idx += 1

        where = " AND ".join(clauses)

        rows = await conn.fetch(
            f"""
            SELECT
                i.user_message,
                i.llm_response,
                i.model,
                i.system_prompt_version,
                f.rating,
                f.correction_kapampangan,
                f.correction_english,
                f.authority_level,
                f.timestamp
            FROM feedback f
            JOIN interactions i ON i.id = f.interaction_id
            WHERE {where}
            ORDER BY f.timestamp ASC
            """,
            *params,
        )
    finally:
        await conn.close()

    total = len(rows)
    exported = 0
    excluded = 0
    records: list[dict] = []

    for row in rows:
        prompt = row["user_message"]
        original_response = row["llm_response"]
        rating = row["rating"]
        correction = row["correction_kapampangan"] or row["correction_english"]

        if args.format == "sft":
            if rating == "thumbs_up":
                # Confirmed correct — use the original response
                records.append({"prompt": prompt, "response": original_response})
                exported += 1
            elif rating == "thumbs_down" and correction:
                # Correction provided — the correction is the preferred response
                records.append({"prompt": prompt, "response": correction})
                exported += 1
            else:
                excluded += 1

        elif args.format == "dpo":
            if rating == "thumbs_down" and correction:
                # chosen = human correction, rejected = model's original output
                records.append({
                    "prompt": prompt,
                    "chosen": correction,
                    "rejected": original_response,
                })
                exported += 1
            else:
                # thumbs_up with no correction has no rejected counterpart for DPO
                excluded += 1

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # Summary
    print(f"\nExport complete — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Format:              {args.format.upper()}")
    print(f"  Min authority level: {args.min_authority_level} (≤{args.min_authority_level} included)")
    if args.after:
        print(f"  After:               {args.after}")
    if args.before:
        print(f"  Before:              {args.before}")
    print(f"  Total records:       {total}")
    print(f"  Exported:            {exported}")
    print(f"  Excluded:            {excluded}")
    print(f"  Output:              {output_path.resolve()}")

    if exported == 0:
        print("\nWARNING: No records were exported. Possible reasons:")
        print("  - No feedback has been reviewed and applied yet")
        print("  - The authority_level filter is too strict")
        if args.format == "dpo":
            print("  - DPO requires thumbs_down feedback with a correction field set")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export approved interaction feedback as training data (SFT or DPO JSONL).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--format",
        choices=["sft", "dpo"],
        default="sft",
        help="Output format: sft (supervised fine-tuning) or dpo (preference pairs). Default: sft",
    )
    parser.add_argument(
        "--min_authority_level",
        type=int,
        choices=[1, 2, 3, 4],
        default=1,
        help=(
            "Include feedback where authority_level <= N. "
            "1=native speaker only, 2=+academic, 3=+community, 4=+LLM inferred. "
            "Default: 1"
        ),
    )
    parser.add_argument(
        "--after",
        default=None,
        metavar="DATE",
        help="Only include feedback after this date (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
    )
    parser.add_argument(
        "--before",
        default=None,
        metavar="DATE",
        help="Only include feedback before this date (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
    )
    parser.add_argument(
        "--output",
        default="training_data.jsonl",
        metavar="FILE",
        help="Output file path. Default: training_data.jsonl",
    )

    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
