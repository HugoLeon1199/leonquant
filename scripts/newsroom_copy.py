#!/usr/bin/env python3
"""Tone down newsroom copy and keep public prose consistently Vietnamese."""

from __future__ import annotations

import re

_HEADLINE_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"^dòng vốn dịch chuyển từ crypto sang cổ phiếu ai\.?$",
            re.I,
        ),
        "Tài sản rủi ro phân hóa khi Bitcoin suy yếu còn nhóm AI vẫn hút chú ý",
    ),
]

_SOFTEN_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"dòng vốn dịch chuyển mạnh mẽ", re.I), "dòng chú ý thị trường nghiêng"),
    (re.compile(r"dịch chuyển mạnh mẽ của dòng vốn toàn cầu", re.I), "xu hướng thị trường gần đây"),
    (re.compile(r"dòng vốn dịch chuyển", re.I), "xu hướng tài sản"),
    (re.compile(r"dòng vốn toàn cầu", re.I), "dòng chú ý thị trường"),
    (re.compile(r"LeonQuant ghi nhận sự", re.I), "48 giờ qua cho thấy"),
    (re.compile(r"ghi nhận sự dịch chuyển mạnh mẽ", re.I), "cho thấy"),
    (re.compile(r"\btoàn cầu\b(?=.*(?:dòng|vốn|dịch chuyển))", re.I), "thị trường"),
]

_PUBLIC_COPY_TRANSLATIONS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\blead stories\b", re.I), "câu chuyện dẫn dắt"),
    (re.compile(r"\bkey angles\b", re.I), "các nhánh chính"),
    (re.compile(r"\bwatch next\b", re.I), "theo dõi tiếp"),
    (re.compile(r"\bwhy it matters\b", re.I), "vì sao quan trọng"),
    (re.compile(r"\bfront page\b", re.I), "trang nhất"),
    (re.compile(r"\bexecutive briefing\b", re.I), "tổng quan 48h"),
    (re.compile(r"\bbig picture\b", re.I), "bức tranh chính"),
    (re.compile(r"\btop stories\b", re.I), "câu chuyện quan trọng nhất"),
    (re.compile(r"\bsector impacts\b", re.I), "tác động theo ngành"),
    (re.compile(r"\bwatch ?24 ?[-–] ?72h\b", re.I), "theo dõi 24-72h tới"),
]

_FILLER_SENTENCE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"[^.!?\n]*\bđể người đọc\b[^.!?\n]*[.!?]", re.I),
    re.compile(r"[^.!?\n]*\bbản tin này gom\b[^.!?\n]*[.!?]", re.I),
    re.compile(r"[^.!?\n]*\bngười đọc cần theo dõi\b[^.!?\n]*[.!?]", re.I),
    re.compile(r"[^.!?\n]*\bbiến số cần theo dõi\b[^.!?\n]*[.!?]", re.I),
    re.compile(r"[^.!?\n]*\bthành từng hồ sơ\b[^.!?\n]*[.!?]", re.I),
    re.compile(r"[^.!?\n]*\bphân tích sự phân hóa của dòng vốn\b[^.!?\n]*[.!?]", re.I),
]


def strip_newsroom_filler(text: str) -> str:
    s = str(text or "").strip()
    if not s:
        return s
    for pat in _FILLER_SENTENCE_PATTERNS:
        s = pat.sub("", s)
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"  +", " ", s)
    return s.strip()


def soften_newsroom_text(text: str) -> str:
    s = str(text or "").strip()
    if not s:
        return s
    for pat, repl in _PUBLIC_COPY_TRANSLATIONS:
        s = pat.sub(repl, s)
    for pat, repl in _HEADLINE_REPLACEMENTS:
        if pat.match(s):
            return repl
    for pat, repl in _SOFTEN_PATTERNS:
        s = pat.sub(repl, s)
    return s


def soften_prose(text: str) -> str:
    """Long-form digest copy: bỏ câu meta và Việt hóa các nhãn công khai."""
    return soften_newsroom_text(strip_newsroom_filler(str(text or "").strip()))


def soften_editor_note(note: str) -> str:
    raw = str(note or "").strip()
    if not raw:
        return ""
    return soften_prose(raw)


def soften_headline(text: str) -> str:
    return soften_newsroom_text(str(text or "").strip())


_ENGLISH_COMMON_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "they",
    "their",
    "will",
    "would",
    "could",
    "should",
    "must",
    "market",
    "markets",
    "deal",
    "agreement",
    "rally",
    "surge",
    "warns",
    "warning",
    "report",
    "reports",
    "source",
    "sources",
    "share",
    "shares",
    "trade",
    "trading",
    "policy",
    "rate",
    "rates",
    "bank",
    "banks",
    "tech",
    "sector",
    "sectors",
    "investors",
    "investor",
    "prices",
    "price",
    "oil",
    "gold",
    "crypto",
}

_VIETNAMESE_DIACRITIC_RE = re.compile(
    r"[àáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệ"
    r"ìíỉĩịòóỏõọôốồổỗộơớờởỡợ"
    r"ùúủũụưứừửữựỳýỷỹỵ]",
    re.I,
)

_ENGLISH_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z'’-]{2,}")


def is_english_heavy_public_copy(text: str) -> bool:
    """Detect public prose that is too English-heavy for the newsroom brief."""
    raw = str(text or "").strip()
    if len(raw) < 48:
        return False
    raw = re.sub(r"https?://\S+", " ", raw)
    tokens = _ENGLISH_TOKEN_RE.findall(raw)
    if len(tokens) < 8:
        return False
    vi_marks = len(_VIETNAMESE_DIACRITIC_RE.findall(raw))
    common_hits = sum(1 for tok in tokens if tok.lower() in _ENGLISH_COMMON_WORDS)
    if common_hits >= 6:
        return True
    if common_hits >= 4 and vi_marks <= 3:
        return True
    if common_hits >= 3 and vi_marks == 0 and len(raw) >= 120:
        return True
    return False


def sanitize_public_prose(text: str, *, fallback: str = "") -> str:
    """Clean public prose and drop it if it is still too English-heavy."""
    s = soften_prose(text)
    if not s:
        return fallback
    if is_english_heavy_public_copy(s):
        return fallback
    return s
