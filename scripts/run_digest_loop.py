#!/usr/bin/env python3
"""Run batch digest one API call at a time (free-tier friendly).

Timing: each step waits for Gemini to finish, then sleeps 60s before the next step
(plus 60s before each API call inside summarize_news_gemini.py).
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIGEST_MODEL = "gemini-3.1-flash-lite"
SUMMARY = ROOT / "gemini_digest_summary.json"
PARTIALS = ROOT / "gemini_digest_partials.json"
LOOP_LOG = ROOT / "gemini_digest_loop.log"
# Free tier: 60s between calls so TPM window can reset (~125k/min).
PAUSE_BETWEEN_STEPS_SEC = 60
FREE_TIER_MAX_INPUT_TOKENS = 100_000
FREE_TIER_SLEEP_SEC = 60


def partial_count() -> int:
    if not PARTIALS.is_file():
        return 0
    data = json.loads(PARTIALS.read_text(encoding="utf-8"))
    return len(data.get("partials") or [])


def expected_total() -> int | None:
    if not PARTIALS.is_file():
        return None
    data = json.loads(PARTIALS.read_text(encoding="utf-8"))
    partials = data.get("partials") or []
    if not partials:
        return None
    return int(partials[0].get("batch_total") or 0) or None


def main() -> int:
    step = 0
    while not SUMMARY.is_file():
        step += 1
        n = partial_count()
        total = expected_total()
        label = f"{n}/{total}" if total else str(n)
        print(f"\n=== Step {step} | partials {label} ===", flush=True)
        with open(LOOP_LOG, "a", encoding="utf-8") as logf:
            rc = subprocess.call(
                [
                    sys.executable,
                    str(ROOT / "summarize_news_gemini.py"),
                    "--input",
                    str(ROOT / "news_for_ai_clean.json"),
                    "--mode",
                    "digest",
                    "--batch-digest",
                    "--model",
                    DIGEST_MODEL,
                    "--max-input-tokens-per-request",
                    str(FREE_TIER_MAX_INPUT_TOKENS),
                    "--use-existing-outline",
                    "--resume-partials",
                    "--max-api-calls",
                    "1",
                    "--min-request-interval",
                    str(FREE_TIER_SLEEP_SEC),
                    "--api-pause",
                    str(FREE_TIER_SLEEP_SEC),
                ],
                cwd=ROOT,
                stdout=logf,
                stderr=subprocess.STDOUT,
            )
        if SUMMARY.is_file():
            print("Done:", SUMMARY)
            return 0
        if rc != 0:
            print(f"Step failed (exit {rc}); wait 5 min for quota...", flush=True)
            time.sleep(300)
            continue
        if partial_count() == n:
            print("No progress this step; wait 5 min...", flush=True)
            time.sleep(300)
            continue
        print(f"Wait {PAUSE_BETWEEN_STEPS_SEC}s before next step...", flush=True)
        time.sleep(PAUSE_BETWEEN_STEPS_SEC)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
