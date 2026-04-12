"""
Drift gate for the gateway artifact generator.

Fails if any MCP service openapi.yaml has been edited since the last
`make generate` run, reminding the developer to regenerate and commit
the updated gateway artifacts (apis/*.json, portal/catalog.json).

Pattern is identical to mcp-vocabulary/tests/test_generated.py.
"""

import hashlib
from pathlib import Path


def _parse_hash_file(hash_path: Path) -> dict[str, str]:
    """Return {relative_path: sha256} from a .spec-hash file."""
    result = {}
    for line in hash_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        sha, path = line.split("  ", 1)
        result[path] = sha
    return result


def test_gateway_artifacts_are_not_stale():
    """gateway/apis/ and gateway/portal/ must match current MCP openapi.yaml files.

    If this test fails: run `make generate` from gateway/ and commit the result
    (updated apis/*.json, portal/catalog.json, and apis/.spec-hash).
    """
    # Locate gateway/ relative to this test file
    gateway_dir = Path(__file__).parent.parent
    monorepo_root = gateway_dir.parent
    hash_path = gateway_dir / "apis" / ".spec-hash"

    assert hash_path.exists(), (
        "gateway/apis/.spec-hash not found. "
        "Run 'make generate' from gateway/ to create it."
    )

    recorded = _parse_hash_file(hash_path)
    assert recorded, "gateway/apis/.spec-hash is empty — run 'make generate'."

    for rel_path, stored_hash in recorded.items():
        spec_path = monorepo_root / rel_path
        assert spec_path.exists(), (
            f"{rel_path} listed in .spec-hash but not found on disk. "
            "Check that monorepo paths are consistent."
        )
        current_hash = hashlib.sha256(spec_path.read_bytes()).hexdigest()
        assert current_hash == stored_hash, (
            f"{rel_path} has changed since gateway/apis/ was last regenerated.\n"
            "Run 'make generate' from gateway/ and commit the result."
        )
