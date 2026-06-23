#!/usr/bin/env python3
"""Run batch digest — parallel-friendly, tận dụng TPM 4M/phút của gemini-3.1-flash-lite.

Mỗi chunk ~40K tokens. TPM limit 4M/phút → chạy 3 chunks/lần an toàn (120K < 4M).
Sau mỗi batch 3 chunks, sleep 30s để tránh burst TPM rồi tiếp tục.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIGEST_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")
SUMMARY = ROOT / "gemini_digest_summary.json"
PARTIALS = ROOT / "gemini_digest_partials.json"
OUTLINE = ROOT / "gemini_digest_outline.json"
LOOP_LOG = ROOT / "gemini_digest_loop.log"
# CI (DIGEST_LOOP_FORCE=1): 3 calls/step để nhanh hơn — free tier local giữ 1
_CI_MODE = bool(os.environ.get("DIGEST_LOOP_FORCE"))
CALLS_PER_STEP = int(os.environ.get("DIGEST_CALLS_PER_STEP", "3" if _CI_MODE else "1"))
PAUSE_BETWEEN_STEPS_SEC = 30 if _CI_MODE else 60
PAUSE_ON_QUOTA_FAIL_SEC = 300
PAUSE_ON_OTHER_FAIL_SEC = 60
FREE_TIER_MAX_INPUT_TOKENS = 40_000
FREE_TIER_SLEEP_SEC = 60
# Giới hạn tổng số bước để tránh loop vô tận khi quota bị block liên tục
MAX_STEPS = int(os.environ.get("DIGEST_LOOP_MAX_STEPS", "80"))
# Chỉ accept gemini_digest_summary.json sau khi có đủ partials
MIN_PARTIALS_BEFORE_MERGE = 2
FATAL_ERROR_MARKERS = (
    "api_key_invalid",
    "api key not found",
    "please pass a valid api key",
    "status=invalid_argument",
    "status=not_found",
    "model not found",
    "unsupported model",
)


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


def recent_log_tail() -> str:
    if not LOOP_LOG.is_file():
        return ""
    return LOOP_LOG.read_text(encoding="utf-8", errors="replace")[-4000:].lower()


def is_fatal_gemini_error(log_tail: str) -> bool:
    return any(marker in log_tail for marker in FATAL_ERROR_MARKERS)


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
        if step > MAX_STEPS:
            print(
                f"ERROR: reached MAX_STEPS={MAX_STEPS} without completing digest. "
                "Likely persistent quota block. Failing CI fast.",
                file=sys.stderr,
                flush=True,
            )
            return 1
        n = partial_count()
        total = expected_total()
        label = f"{n}/{total}" if total else str(n)
        print(f"\n=== Step {step}/{MAX_STEPS} | partials {label} ===", flush=True)
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
            str(CALLS_PER_STEP),
            "--api-pause",
            str(FREE_TIER_SLEEP_SEC),
        ]
        if OUTLINE.is_file():
            cmd.append("--use-existing-outline")
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
            tail = recent_log_tail()
            if is_fatal_gemini_error(tail):
                print(
                    "Fatal Gemini configuration error detected in digest loop log. "
                    "Stop retrying so CI fails fast instead of timing out.",
                    file=sys.stderr,
                    flush=True,
                )
                return rc
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
