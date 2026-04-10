#!/usr/bin/env python3
"""
package_contribution.py — Package a contributor's export into a zip archive.

Used in Mode 2 (maintainer-mediated sync) when contributors cannot or should
not use git directly. The resulting zip is sent to the maintainer who runs
merge_contributions.py to incorporate the changes.

Usage:
    python scripts/package_contribution.py \\
        --input contrib/ \\
        --contributor "Maria Santos" \\
        --output maria_2024_03_15_contribution.zip
"""

import argparse
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path


REQUIRED_FILES = [
    "contrib_vocabulary.json",
    "contrib_grammar_nodes.json",
    "contrib_grammar_edges.json",
    "manifest.json",
]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Package contribution export files into a zip archive"
    )
    parser.add_argument("--input", default="contrib/", metavar="DIR",
                        help="Directory containing contribution export files (default: contrib/)")
    parser.add_argument("--contributor", required=True, metavar="NAME",
                        help="Contributor name (used to update the manifest and name the output file)")
    parser.add_argument("--output", metavar="FILE",
                        help="Output zip file path (default: {contributor}_{date}_contribution.zip)")
    args = parser.parse_args()

    input_dir = Path(args.input)
    if not input_dir.exists():
        print(f"Error: input directory '{input_dir}' does not exist.", file=sys.stderr)
        print("Run export_contributions.py first to generate contribution files.", file=sys.stderr)
        sys.exit(1)

    # Check required files exist
    missing = [f for f in REQUIRED_FILES if not (input_dir / f).exists()]
    if missing:
        print(f"Error: missing files in '{input_dir}': {', '.join(missing)}", file=sys.stderr)
        print("Run export_contributions.py first to generate contribution files.", file=sys.stderr)
        sys.exit(1)

    # Determine output filename
    if args.output:
        output_path = Path(args.output)
    else:
        date_str = datetime.now(timezone.utc).strftime("%Y_%m_%d")
        safe_name = args.contributor.lower().replace(" ", "_").replace("/", "_")
        output_path = Path(f"{safe_name}_{date_str}_contribution.zip")

    # Load manifest to get entry counts, update contributor name
    manifest_path = input_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["contributor"] = args.contributor
    manifest["packaged_at"] = datetime.now(timezone.utc).isoformat()

    counts = manifest.get("counts", {})
    vocab_count = counts.get("vocabulary", 0)
    nodes_count = counts.get("grammar_nodes", 0)
    edges_count = counts.get("grammar_edges", 0)

    # Write zip
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Write updated manifest with corrected contributor name
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))

        for filename in REQUIRED_FILES:
            if filename == "manifest.json":
                continue  # already written above
            file_path = input_dir / filename
            zf.write(file_path, arcname=filename)

    print(f"Packaged {vocab_count} vocabulary entries, "
          f"{nodes_count} grammar nodes, {edges_count} grammar edges")
    print(f"Output: {output_path}")
    print()
    print(f"Send this file to the maintainer for review and merging.")
    print()
    print("Maintainer instructions:")
    print(f"  1. Unzip to a temp directory: unzip {output_path} -d /tmp/{safe_name if not args.output else 'contribution'}/")
    print(f"  2. Run merge: python scripts/merge_contributions.py "
          f"--canonical data/ --contributions /tmp/{safe_name if not args.output else 'contribution'}/ "
          f"--output data/ --report merge_report.md")
    print(f"  3. Review merge_report.md and commit data/ if satisfied")


if __name__ == "__main__":
    safe_name = ""  # hoisted for error message use
    main()
