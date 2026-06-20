#!/usr/bin/env python3
"""Run batch digest one API call at a time (free-tier friendly).

Timing: each step waits for Gemini to finish, then sleeps 60s before the next step
(plus 60s before each API call inside summarize_news_gemini.py).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIGEST_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
SUMMARY = ROOT / "gemini_digest_summary.json"
PARTIALS = ROOT / "gemini_digest_partials.json"
LOOP_LOG = ROOT / "gemini_digest_loop.log"
# Free tier: 30s between successful steps (flash-8b có quota cao hơn, ít cần chờ).
PAUSE_BETWEEN_STEPS_SEC = 30
# Chỉ chờ lâu khi Gemini báo quota/rate-limit; lỗi khác (code, mạng) thử lại sau 60s.
PAUSE_ON_QUOTA_FAIL_SEC = 300
PAUSE_ON_OTHER_FAIL_SEC = 60
# 100k token/chunk → ~10 chunks từ 800+ bài (TPM free tier 125k/min, mỗi chunk ~1 phút)
FREE_TIER_MAX_INPUT_TOKENS = 100_000
FREE_TIER_SLEEP_SEC = 30
# Chỉ accept gemini_digest_summary.json sau khi có đủ partials (tránh summary sinh sớm từ chunk đầu)
MIN_PARTIALS_BEFORE_MERGE = 2


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
    if not (ROOT / "news_for_ai_clean.json").is_file():
        print("ERROR: missing news_for_ai_clean.json — run export + clean first.", file=sys.stderr)
        return 2
    if SUMMARY.is_file() and not os.environ.get("DIGEST_LOOP_FORCE"):
        print(
            "gemini_digest_summary.json already exists; skip digest loop.\n"
            "  CI: workflow removes it before this step.\n"
            "  Local fresh run: delete the file or set DIGEST_LOOP_FORCE=1",
            file=sys.stderr,
        )
        return 0
    step = 0
    while not SUMMARY.is_file():
        step += 1
        n = partial_count()
        total = expected_total()
        label = f"{n}/{total}" if total else str(n)
        print(f"\n=== Step {step} | partials {label} ===", flush=True)
        cmd = [
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
            "--resume-partials",
            "--max-api-calls",
            "1",
            "--api-pause",
            str(FREE_TIER_SLEEP_SEC),
        ]
        with open(LOOP_LOG, "a", encoding="utf-8") as logf:
            proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
            for line in proc.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
                logf.write(line)
            rc = proc.wait()
        if SUMMARY.is_file():
            pc = partial_count()
            if pc >= MIN_PARTIALS_BEFORE_MERGE:
                print("Done:", SUMMARY)
                return 0
            # Summary sinh quá sớm (chỉ 1 chunk) — xóa để loop chạy thêm batch
            SUMMARY.unlink()
            print(
                f"[loop] Summary appeared early ({pc} partial(s) < {MIN_PARTIALS_BEFORE_MERGE} required). "
                "Deleted, continuing to accumulate more chunks...",
                flush=True,
            )
            time.sleep(PAUSE_BETWEEN_STEPS_SEC)
            continue
        if rc != 0:
            tail = ""
            if LOOP_LOG.is_file():
                tail = LOOP_LOG.read_text(encoding="utf-8", errors="replace")[-4000:].lower()
            quota_hit = any(
                x in tail
                for x in ("429", "quota", "rate limit", "resource exhausted", "too many requests")
            )
            wait = PAUSE_ON_QUOTA_FAIL_SEC if quota_hit else PAUSE_ON_OTHER_FAIL_SEC
            why = "quota" if quota_hit else "other"
            print(f"Step failed (exit {rc}); wait {wait}s ({why})...", flush=True)
            time.sleep(wait)
            continue
        if partial_count() == n:
            print(f"No progress this step; wait {PAUSE_ON_OTHER_FAIL_SEC}s...", flush=True)
            time.sleep(PAUSE_ON_OTHER_FAIL_SEC)
            continue
        print(f"Wait {PAUSE_BETWEEN_STEPS_SEC}s before next step...", flush=True)
        time.sleep(PAUSE_BETWEEN_STEPS_SEC)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
