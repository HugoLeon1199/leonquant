#!/usr/bin/env python3
"""Move sectionPulse/sectionInvest out of #brief into #pulse / #invest sections."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "landing_page.html"


def main() -> None:
    html = PAGE.read_text(encoding="utf-8")

    m_sync = re.search(
        r'(<section id="brief"[^>]*>\s*<div class="container">)\s*'
        r'(<p id="syncNote"[^>]*>.*?</p>)',
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
        r'(<div id="sectionInvest" class="brief-block">[\s\S]*?)(?=\s*</div>\s*</section>\s*<section id="reference")',
        html,
    )
    if not (m_thesis and m_pulse and m_invest):
        raise SystemExit("Could not split sectionThesis / sectionPulse / sectionInvest")

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
    # consume closing </div></section> after invest inside old brief
    tail_m = re.match(r"\s*</div>\s*</section>", html[end:])
    end = end + (tail_m.end() if tail_m else 0)

    html_new = html[:start] + new_brief + html[end:]

    if "body.digest-mode #brief #sectionPulse" not in html_new:
        html_new = html_new.replace(
            "body.digest-mode #invest { display: none !important; }",
            "body.digest-mode #brief #sectionPulse,\n"
            "    body.digest-mode #brief #sectionInvest { display: none !important; }\n"
            "    body.digest-mode #invest { display: none !important; }",
            1,
        )

    PAGE.write_text(html_new, encoding="utf-8")
    print("OK: restored #pulse and #invest sections; #brief has sectionThesis only.")


if __name__ == "__main__":
    main()
