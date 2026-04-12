"""
Drift check for the contract-first codegen.

Fails if api/openapi.yaml has been edited since the last `make generate` run,
reminding the developer to regenerate and commit the updated stubs.

The check works by comparing a SHA-256 of the live spec file against a hash
recorded in api/_generated/.spec-hash at generation time. No Docker-in-Docker
or network access required — runs entirely in the test container.
"""

import hashlib
from pathlib import Path


def test_generated_code_is_not_stale():
    """api/_generated/ must be up to date with api/openapi.yaml.

    If this test fails: run `make generate` from mcp-vocabulary/ and commit
    the result (both the regenerated files and the updated .spec-hash).
    """
    spec_path = Path("api/openapi.yaml")
    hash_path = Path("api/_generated/.spec-hash")

    assert spec_path.exists(), "api/openapi.yaml not found — is the source volume mounted?"
    assert hash_path.exists(), (
        "api/_generated/.spec-hash not found. "
        "Run 'make generate' to create it."
    )

    current_hash = hashlib.sha256(spec_path.read_bytes()).hexdigest()
    stored_hash = hash_path.read_text().strip()

    assert current_hash == stored_hash, (
        "api/openapi.yaml has changed since api/_generated/ was last regenerated.\n"
        "Run 'make generate' from mcp-vocabulary/ and commit the result."
    )
