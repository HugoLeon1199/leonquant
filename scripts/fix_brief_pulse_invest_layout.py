#!/usr/bin/env python3
"""Ensure #pulse and #invest are sibling sections; invest must not live inside #pulse."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PAGE = ROOT / "landing_page.html"


def _ensure_digest_css(html: str) -> str:
    needle = "body.digest-mode #brief #sectionPulse"
    if needle in html:
        return html
    return html.replace(
        "body.digest-mode #invest { display: none !important; }",
        "body.digest-mode #brief #sectionPulse,\n"
        "    body.digest-mode #brief #sectionInvest { display: none !important; }\n"
        "    body.digest-mode #invest { display: none !important; }",
        1,
    )


def _split_invest_from_pulse(html: str) -> str:
    if re.search(r'<section id="invest"', html, re.I):
        return html

    m = re.search(
        r'<section id="pulse"([^>]*)>\s*<div class="container">\s*'
        r'(<div id="sectionPulse"[^>]*>[\s\S]*?</div>)\s*'
        r'(<div id="sectionInvest"[^>]*>[\s\S]*?</div>)\s*'
        r'</div>\s*</section>\s*'
        r'(<section id="reference")',
        html,
        re.DOTALL | re.I,
    )
    if not m:
        raise SystemExit("Could not find sectionInvest inside #pulse to split")

    _pulse_attrs, pulse_block, invest_block, ref_open = m.groups()

    replacement = (
        f'    <section id="pulse" class="alt" hidden data-embedded-pulse="1">\n'
        f"      <div class=\"container\">\n        {pulse_block.strip()}\n"
        f"      </div>\n    </section>\n\n"
        f'    <section id="invest" class="alt" hidden>\n'
        f"      <div class=\"container\">\n        {invest_block.strip()}\n"
        f"      </div>\n    </section>\n\n    {ref_open}"
    )
    return html[: m.start()] + replacement + html[m.end() :]


def _split_all_from_brief(html: str) -> str:
    """Legacy: pulse + invest still inside #brief."""
    m_sync = re.search(
        r'(<section id="brief"[^>]*>\s*<div class="container">)\s*'
        r"(<p id=\"syncNote\"[^>]*>.*?</p>)",
        html,
        re.DOTALL,
    )
    if not m_sync:
        raise SystemExit("syncNote / brief container not found")

    m_thesis = re.search(
        r'(<div id="sectionThesis" class="brief-block">[\s\S]*?)(?=<div id="sectionPulse")',
        html,
    )
    m_pulse = re.search(
        r'(<div id="sectionPulse"[^>]*>[\s\S]*?)(?=<div id="sectionInvest")',
        html,
    )
    m_invest = re.search(
        r'(<div id="sectionInvest" class="brief-block">[\s\S]*?)'
        r"(?=\s*</div>\s*</section>\s*<section id=\"reference\")",
        html,
    )
    if not (m_thesis and m_pulse and m_invest):
        raise SystemExit("Could not split sectionThesis / sectionPulse / sectionInvest in #brief")

    brief_open, sync_note = m_sync.groups()
    thesis_block = m_thesis.group(1).strip()
    pulse_block = m_pulse.group(1).strip()
    invest_block = m_invest.group(1).strip()

    pulse_section = f"""    <section id="pulse" class="alt" hidden data-embedded-pulse="1">
      <div class="container">
        {pulse_block}
      </div>
    </section>

    <section id="invest" class="alt" hidden>
      <div class="container">
        {invest_block}
      </div>
    </section>
"""

    new_brief = f"""{brief_open}
        {sync_note.strip()}
        {thesis_block}
      </div>
    </section>

{pulse_section}"""

    start = m_sync.start()
    end = m_invest.end()
    tail_m = re.match(r"\s*</div>\s*</section>", html[end:])
    end = end + (tail_m.end() if tail_m else 0)

    return html[:start] + new_brief + html[end:]


def main() -> None:
    import sys

    page = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_PAGE
    html = page.read_text(encoding="utf-8")

    if re.search(r'<section id="invest"', html, re.I):
        html = re.sub(
            r'<section id="pulse"([^>]*)>',
            lambda m: (
                '<section id="pulse"'
                + re.sub(r'\s*data-embedded-pulse="1"', "", m.group(1), flags=re.I)
                + ' hidden data-embedded-pulse="1">'
            ),
            html,
            count=1,
            flags=re.I,
        )
        print("OK: #invest exists; normalized #pulse hidden flag.")
    elif re.search(
        r'<section id="pulse"[^>]*>[\s\S]*?<div id="sectionInvest"',
        html,
        re.I,
    ):
        html = _split_invest_from_pulse(html)
        print("OK: moved sectionInvest out of #pulse into #invest section.")
    else:
        html = _split_all_from_brief(html)
        print("OK: restored #pulse and #invest from #brief.")

    html = _ensure_digest_css(html)
    html = re.sub(
        r'(<section id="pulse"[^>]*)\s*data-embedded-pulse="1"\s*data-embedded-pulse="1"',
        r'\1 data-embedded-pulse="1"',
        html,
        count=1,
        flags=re.I,
    )
    page.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
