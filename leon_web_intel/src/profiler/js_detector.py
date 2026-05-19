"""Heuristic detection for JavaScript-rendered pages."""

from __future__ import annotations

from profiler.html_probe import HTMLProbeResult
from settings import CrawlRules


def detect_js_heavy(html: str, probe: HTMLProbeResult, rules: CrawlRules) -> bool:
    cfg = rules.js_detection
    signals = 0

    if probe.html_text_length < cfg.min_text_length:
        signals += 1

    if probe.script_count > cfg.script_count_threshold:
        signals += 1

    if probe.sample_extracted_text_length < rules.min_extract_text_length:
        signals += 1

    lower = html.lower()
    for kw in cfg.js_keywords:
        if kw.lower() in lower:
            signals += 1
            break

    if probe.html_link_count < 12 and probe.script_count >= max(8, cfg.script_count_threshold // 2):
        signals += 1

    return signals >= 2
