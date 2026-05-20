#!/usr/bin/env python3
"""
Preflight checks before full batch digest (gemini-3.1-flash-lite, ~100k/request, free TPM).

Steps:
  1. API key + model ping (tiny JSON)
  2. Dry-run: chunk count & token estimates
  3. Mini chunk: 2 articles, same prompt shape as production
  4. Optional --live-chunk: one real chunk-1 API call at 200k budget

Usage:
  python scripts/test_gemini_digest_preflight.py
  python scripts/test_gemini_digest_preflight.py --live-chunk
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from summarize_news_gemini import (  # noqa: E402
    build_digest_chunk_prompt,
    call_gemini,
    chunk_enriched_articles_by_tokens,
    compact_for_gemini,
    enrich_articles,
    estimate_digest_chunk_prompt_tokens,
    estimate_tokens_from_chars,
    load_env_file,
    load_existing_outline,
    load_json,
    parse_gemini_json_text,
    resolve_max_input_tokens_per_request,
)

MODEL = "gemini-3.1-flash-lite"
MAX_INPUT = 100_000
INPUT_JSON = ROOT / "news_for_ai_clean.json"
OUTLINE_JSON = ROOT / "gemini_digest_outline.json"
PARTIALS_JSON = ROOT / "gemini_digest_partials.json"


def ping(key: str) -> bool:
    print("\n[1] Ping model (tiny JSON)...")
    try:
        out = call_gemini(
            'Reply JSON only: {"status":"ok","model":"gemini-3.1-flash-lite"}',
            MODEL,
            key,
            timeout=90,
            min_retry_interval=0,
            max_output_tokens=256,
        )
        print(f"    OK: {out}")
        return True
    except Exception as exc:
        print(f"    FAIL: {exc}")
        return False


def dry_run_plan(payload: dict) -> int:
    print("\n[2] Dry-run plan (no API)...")
    articles = payload.get("articles") or []
    window = payload.get("window") or {}
    outline = load_existing_outline(OUTLINE_JSON)
    enriched = enrich_articles(
        articles, 0, 0, 20, refetch_urls=False, quiet=True
    )
    cap = resolve_max_input_tokens_per_request(MODEL, MAX_INPUT, 0)
    chunks = chunk_enriched_articles_by_tokens(
        enriched,
        cap,
        total_articles=len(articles),
        window_meta=window,
        global_outline=outline,
    )
    print(f"    Articles: {len(articles)}")
    print(f"    Cap: {cap} input tokens/request")
    print(f"    Chunks: {len(chunks)} (+ 1 merge; outline {'yes' if outline else 'no'})")
    if chunks:
        est = estimate_digest_chunk_prompt_tokens(
            chunks[0],
            batch_index=1,
            batch_total=len(chunks),
            total_articles=len(articles),
            window_meta=window,
            global_outline=outline,
        )
        print(f"    Chunk 1: {len(chunks[0])} articles, prompt ~{est} tokens")
    check_partials_compat(len(chunks))
    return len(chunks)


def check_partials_compat(expected_total: int) -> None:
    if not PARTIALS_JSON.is_file():
        return
    data = json.loads(PARTIALS_JSON.read_text(encoding="utf-8"))
    partials = data.get("partials") or []
    if not partials:
        return
    old_total = int(partials[0].get("batch_total") or 0)
    n = len(partials)
    if old_total and old_total != expected_total:
        print(
            f"\n    WARNING: gemini_digest_partials.json has {n}/{old_total} "
            f"but 200k plan needs {expected_total} chunks."
        )
        print("    Backup partials before restart, or resume only if batch_total matches.")


def mini_chunk_test(key: str, payload: dict) -> bool:
    print("\n[3] Mini chunk (2 articles, production prompt shape)...")
    articles = (payload.get("articles") or [])[:2]
    window = payload.get("window") or {}
    outline = load_existing_outline(OUTLINE_JSON)
    enriched = enrich_articles(articles, 0, 0, 20, refetch_urls=False, quiet=True)
    prompt = build_digest_chunk_prompt(
        enriched,
        batch_index=1,
        batch_total=99,
        total_articles=len(payload.get("articles") or []),
        window_meta=window,
        global_outline=outline,
    )
    est = estimate_tokens_from_chars(len(prompt))
    print(f"    Prompt ~{est} tokens ({len(prompt)} chars)")
    try:
        out = call_gemini(
            prompt,
            MODEL,
            key,
            timeout=300,
            min_retry_interval=0,
            max_output_tokens=4096,
        )
        required = {"batch_index", "sector_notes"}
        missing = required - set(out.keys())
        if missing:
            print(f"    FAIL: JSON missing keys {missing}")
            return False
        parse_gemini_json_text(json.dumps(out, ensure_ascii=False))
        print(f"    OK: sector_notes={len(out.get('sector_notes') or [])}")
        return True
    except Exception as exc:
        print(f"    FAIL: {exc}")
        return False


def live_chunk_test(key: str, payload: dict) -> bool:
    print("\n[4] Live chunk 1 (real size, 200k budget)...")
    articles = payload.get("articles") or []
    window = payload.get("window") or {}
    outline = load_existing_outline(OUTLINE_JSON)
    enriched = enrich_articles(
        articles, 0, 0, 20, refetch_urls=False, quiet=True
    )
    cap = resolve_max_input_tokens_per_request(MODEL, MAX_INPUT, 0)
    chunks = chunk_enriched_articles_by_tokens(
        enriched,
        cap,
        total_articles=len(articles),
        window_meta=window,
        global_outline=outline,
    )
    if not chunks:
        print("    FAIL: no chunks")
        return False
    chunk = chunks[0]
    prompt = build_digest_chunk_prompt(
        chunk,
        batch_index=1,
        batch_total=len(chunks),
        total_articles=len(articles),
        window_meta=window,
        global_outline=outline,
    )
    est = estimate_tokens_from_chars(len(prompt))
    print(f"    Chunk 1: {len(chunk)} articles, prompt ~{est} tokens")
    if est > cap:
        print(f"    FAIL: prompt {est} > cap {cap}")
        return False
    try:
        out = call_gemini(
            prompt,
            MODEL,
            key,
            timeout=1800,
            min_retry_interval=60,
            max_output_tokens=16_384,
        )
        print(f"    OK: keys={list(out.keys())[:6]}...")
        return True
    except Exception as exc:
        print(f"    FAIL: {exc}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight digest (flash-lite 200k)")
    parser.add_argument(
        "--live-chunk",
        action="store_true",
        help="Call API with real chunk 1 (~200k input); costs quota",
    )
    parser.add_argument("--input", type=Path, default=INPUT_JSON)
    args = parser.parse_args()

    load_env_file(ROOT / ".env")
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        print("GEMINI_API_KEY missing", file=sys.stderr)
        return 2
    if not args.input.is_file():
        print(f"Input not found: {args.input}", file=sys.stderr)
        return 2

    payload = load_json(args.input)
    print(f"Preflight: model={MODEL}, max_input={MAX_INPUT}, input={args.input.name}")

    ok = True
    ok = ping(key) and ok
    dry_run_plan(payload)
    ok = mini_chunk_test(key, payload) and ok
    if args.live_chunk:
        ok = live_chunk_test(key, payload) and ok
    else:
        print("\n[4] Skipped live chunk 1 (pass --live-chunk to test ~200k request)")

    print("\n" + ("PASS" if ok else "FAIL — fix before full digest"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
