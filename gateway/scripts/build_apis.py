"""
build_apis.py — Generate gateway artifacts from MCP service OpenAPI specs.

For each MCP service that has api/openapi.yaml, emits:
  1. gateway/apis/{service}.json   — Tyk Classic API definition
  2. gateway/portal/catalog.json  — Scalar multi-spec catalog config

Run from gateway/ or from the monorepo root:
    python3 gateway/scripts/build_apis.py
    cd gateway && make generate

Also writes gateway/apis/.spec-hash (one SHA-256 per source file) used by
the drift gate (make check-generated + tests/test_drift.py).
"""

import hashlib
import json
import sys
from pathlib import Path


def _make_object_id(s: str) -> str:
    """Derive a deterministic 24-char hex MongoDB ObjectId from a string.

    Tyk Classic API definitions require 'id' to be a valid ObjectId.
    We use the first 24 hex chars of the MD5 of the service name so the
    value is stable across regenerations and unique per service.
    """
    return hashlib.md5(s.encode()).hexdigest()[:24]

# ---------------------------------------------------------------------------
# Service registry
# Each entry: (service_dir_name, listen_path_prefix, target_host, target_port)
# Add mcp-grammar here when it gains an api/openapi.yaml.
# ---------------------------------------------------------------------------
SERVICES = [
    {
        "dir": "mcp-vocabulary",
        "listen_path": "/vocab/",
        "target_host": "mcp-vocabulary",
        "target_port": 8001,
        "gateway_host": "localhost",
        "gateway_port": 8080,
    },
]

SCRIPT_DIR = Path(__file__).parent
GATEWAY_DIR = SCRIPT_DIR.parent

# Support two invocation contexts:
#  1. Docker container: script at /monorepo/gateway/scripts/build_apis.py
#     MONOREPO_ROOT = /monorepo  (GATEWAY_DIR.parent)
#  2. Host (if pyyaml is installed locally): script at <repo>/gateway/scripts/
#     MONOREPO_ROOT = <repo>     (GATEWAY_DIR.parent)
# Both are handled by the same expression since GATEWAY_DIR.parent always
# points one level above gateway/, regardless of the mount point.
MONOREPO_ROOT = GATEWAY_DIR.parent

APIS_DIR = GATEWAY_DIR / "apis"
PORTAL_DIR = GATEWAY_DIR / "portal"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_tyk_api_def(service: dict, openapi: dict) -> dict:
    """Produce a Tyk Classic API definition dict from an OpenAPI spec."""
    api_id = service["dir"]
    object_id = _make_object_id(api_id)  # 24-char hex required by Tyk's ObjectId field
    name = openapi.get("info", {}).get("title", service["dir"])
    target_url = f"http://{service['target_host']}:{service['target_port']}/"

    # Gather tags from the spec for metadata
    tags = [t["name"] for t in openapi.get("tags", [])]
    tags = list(dict.fromkeys(["mcp", *tags]))  # dedupe, mcp first

    return {
        "id": object_id,
        "name": name,
        "org_id": "default",
        "api_id": api_id,
        "auth": {
            "auth_header_name": "Authorization"
        },
        "use_keyless": True,
        "use_oauth2": False,
        "use_basic_auth": False,
        "proxy": {
            # listen_path lives inside proxy in Tyk's Classic APIDefinition struct.
            # strip_listen_path removes the prefix before forwarding to target_url.
            "listen_path": service["listen_path"],
            "target_url": target_url,
            "strip_listen_path": True,
            "enable_load_balancing": False,
            "target_list": [],
            "check_host_against_uptime_tests": False,
        },
        "active": True,
        "tags": tags,
        "CORS": {
            "enable": True,
            "allowed_origins": ["*"],
            "allowed_methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
            "allowed_headers": [
                "Origin", "X-Requested-With", "Content-Type", "Accept", "Authorization"
            ],
            "exposed_headers": [],
            "allow_credentials": False,
            "max_age": 24,
            "options_passthrough": False,
            "debug": False,
        },
        "version_data": {
            "not_versioned": True,
            "default_version": "Default",
            "versions": {
                "Default": {
                    "name": "Default",
                    "use_extended_paths": True,
                    "extended_paths": {}
                }
            }
        }
    }


def build_scalar_source(service: dict, openapi: dict) -> dict:
    """Produce one Scalar sources entry for the catalog."""
    name = openapi.get("info", {}).get("title", service["dir"])
    slug = service["dir"]
    gateway_base = f"http://{service['gateway_host']}:{service['gateway_port']}"
    spec_url = f"{gateway_base}{service['listen_path']}openapi.json"
    return {
        "title": name,
        "slug": slug,
        "url": spec_url,
        "default": True,
    }


def main() -> None:
    APIS_DIR.mkdir(exist_ok=True)
    PORTAL_DIR.mkdir(exist_ok=True)

    import yaml  # available in the mcp-vocabulary image; or: pip install pyyaml

    spec_hashes: list[str] = []
    scalar_sources: list[dict] = []

    for service in SERVICES:
        spec_path = MONOREPO_ROOT / service["dir"] / "api" / "openapi.yaml"
        if not spec_path.exists():
            print(f"  skip {service['dir']}: no api/openapi.yaml found", file=sys.stderr)
            continue

        print(f"  processing {service['dir']} ({spec_path.relative_to(MONOREPO_ROOT)})")
        openapi = yaml.safe_load(spec_path.read_text())

        # 1. Tyk API definition
        api_def = build_tyk_api_def(service, openapi)
        api_out = APIS_DIR / f"{service['dir']}.json"
        api_out.write_text(json.dumps(api_def, indent=2) + "\n")
        print(f"    → {api_out.relative_to(GATEWAY_DIR)}")

        # 2. Scalar catalog source
        scalar_sources.append(build_scalar_source(service, openapi))

        # 3. Record hash
        spec_hashes.append(f"{sha256_file(spec_path)}  {spec_path.relative_to(MONOREPO_ROOT)}")

    # Write Scalar catalog
    catalog_out = PORTAL_DIR / "catalog.json"
    catalog = {"sources": scalar_sources}
    catalog_out.write_text(json.dumps(catalog, indent=2) + "\n")
    print(f"    → {catalog_out.relative_to(GATEWAY_DIR)}")

    # Write spec-hash file (one SHA-256 + path per line)
    hash_out = APIS_DIR / ".spec-hash"
    hash_out.write_text("\n".join(spec_hashes) + "\n")
    print(f"    → {hash_out.relative_to(GATEWAY_DIR)}")

    print(f"\nDone. {len(scalar_sources)} service(s) registered.")


if __name__ == "__main__":
    main()
