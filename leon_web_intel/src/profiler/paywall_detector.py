"""Keyword-based detection for paywall / login / CAPTCHA signals."""

from __future__ import annotations

from dataclasses import dataclass

from settings import CrawlRules


@dataclass
class PaywallSignals:
    paywall_detected: bool
    login_detected: bool
    captcha_detected: bool


def detect_paywall_signals(html: str, rules: CrawlRules) -> PaywallSignals:
    lower = html.lower()

    def match_any(keywords: list[str]) -> bool:
        return any(k.lower() in lower for k in keywords)

    paywall = match_any(rules.paywall_keywords)
    login = match_any(rules.login_keywords)
    captcha = match_any(rules.captcha_keywords)

    return PaywallSignals(
        paywall_detected=paywall,
        login_detected=login,
        captcha_detected=captcha,
    )
