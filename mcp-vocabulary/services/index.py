"""
Vocabulary index service.

Loads vocabulary.json at startup and builds three indexes for fast lookup:
  - exact:  word (lowercase) → entry
  - forms:  any inflected form → entry
  - gloss:  each English gloss word → list of entries

The JSON schema matches the kaikki.org / Wiktionary extract produced by
scripts/fetch-kaikki.mjs in the frontend source tree.
"""

import json
import logging
import re
import time
from pathlib import Path
from typing import Optional
from opentelemetry import trace
from opentelemetry.trace import StatusCode

from metrics import VOCABULARY_LOOKUPS_TOTAL, VOCABULARY_LOOKUP_DURATION

log = logging.getLogger(__name__)

tracer = trace.get_tracer(__name__)

VOCAB_PATH = "/app/data/vocabulary.json"

_entries: list[dict] = []
_exact_index: dict[str, dict] = {}
_form_index: dict[str, dict] = {}
_gloss_index: dict[str, list[dict]] = {}

_STOP_WORDS = {
    "the", "and", "for", "are", "but", "not", "you", "all", "can",
    "was", "one", "our", "out", "day", "get", "has", "him", "his",
    "man", "new", "now", "old", "see", "two", "way", "who", "did",
    "let", "put", "say", "she", "too", "use", "that", "this", "with",
    "have", "from", "they", "will", "been", "than", "what", "when",
    "would", "there", "their", "about", "into", "more", "some",
}


def load() -> None:
    global _entries, _exact_index, _form_index, _gloss_index

    path = Path(VOCAB_PATH)
    if not path.exists():
        log.warning("vocabulary file not found", extra={"path": VOCAB_PATH})
        return

    with open(path, encoding="utf-8") as f:
        _entries = json.load(f)
    log.info("vocabulary index loaded", extra={"path": VOCAB_PATH, "entries": len(_entries)})

    _exact_index = {}
    _form_index = {}
    _gloss_index = {}

    for entry in _entries:
        word = entry.get("word", "")
        _exact_index[word.lower()] = entry

        for form in entry.get("forms", []):
            form_str = form.get("form", "").lower()
            if form_str:
                _form_index[form_str] = entry

        for gloss in entry.get("glosses", []):
            words = re.sub(r"[^\w\s]", " ", gloss.lower()).split()
            for w in words:
                if len(w) > 2 and w not in _STOP_WORDS:
                    _gloss_index.setdefault(w, []).append(entry)


def lookup(term: str, limit: int = 6) -> list[dict]:
    """Return up to `limit` entries relevant to `term`."""
    with tracer.start_as_current_span("vocabulary.search") as span:
        span.set_attribute("kapampangan.term", term)
        span.set_attribute("kapampangan.limit", limit)
        try:
            t0 = time.time()
            results = _lookup(term, limit)
            duration = time.time() - t0

            span.set_attribute("kapampangan.result_found", len(results) > 0)
            span.set_attribute("kapampangan.result_count", len(results))

            ctx = span.get_span_context()
            exemplar = {"TraceID": trace.format_trace_id(ctx.trace_id)} if ctx.is_valid else None
            VOCABULARY_LOOKUP_DURATION.observe(duration, exemplar=exemplar)
            VOCABULARY_LOOKUPS_TOTAL.labels(
                result="found" if results else "not_found"
            ).inc(exemplar=exemplar)

            log.info(
                "vocabulary lookup",
                extra={"term": term, "found": len(results) > 0, "count": len(results), "duration_s": round(duration, 4)},
            )
            return results
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.record_exception(e)
            log.error("vocabulary lookup error", extra={"term": term, "error": str(e)})
            raise


def _lookup(term: str, limit: int) -> list[dict]:
    """Internal lookup implementation."""
    term_lower = term.lower().strip()

    # 1. Exact match
    if term_lower in _exact_index:
        return [_exact_index[term_lower]]

    # 2. Inflected form match
    if term_lower in _form_index:
        return [_form_index[term_lower]]

    # 3. Prefix match
    prefix_hits = [e for w, e in _exact_index.items() if w.startswith(term_lower)]

    # 4. English gloss match
    gloss_hits: list[dict] = []
    tokens = [w for w in term_lower.split() if len(w) > 2 and w not in _STOP_WORDS]
    seen: set[str] = set()
    for token in tokens:
        for entry in _gloss_index.get(token, []):
            word = entry.get("word", "")
            if word not in seen:
                seen.add(word)
                gloss_hits.append(entry)

    results: list[dict] = []
    seen_all: set[str] = set()
    for entry in prefix_hits + gloss_hits:
        word = entry.get("word", "")
        if word not in seen_all:
            seen_all.add(word)
            results.append(entry)
        if len(results) >= limit:
            break

    return results


def entry_count() -> int:
    return len(_entries)
