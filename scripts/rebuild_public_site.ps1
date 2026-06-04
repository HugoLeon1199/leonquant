# Dựng lại digest web: finalize → content.json → nhúng HTML (GitHub Pages).
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host "== finalize gemini_digest_summary (URL whitelist + hints) =="
python -c @"
import json
from pathlib import Path
from summarize_news_gemini import (
    DEFAULT_DIGEST_OUTPUT_FILE,
    DEFAULT_INPUT_FILE,
    finalize_digest_summary,
    enrich_articles,
    load_json,
)
payload = load_json(DEFAULT_INPUT_FILE)
enriched = enrich_articles(payload.get('articles') or [], 0, 1200, 8, refetch_urls=False, quiet=True)
w = load_json(DEFAULT_DIGEST_OUTPUT_FILE)
w['summary'] = finalize_digest_summary(w['summary'], input_articles=enriched)
DEFAULT_DIGEST_OUTPUT_FILE.write_text(json.dumps(w, ensure_ascii=False, indent=2), encoding='utf-8')
print('OK gemini_digest_summary.json')
"@

Write-Host "== build content.json =="
python build_website_content.py --skip-images
python validate_content.py --content-only

Write-Host "== embed into landing_page.html =="
node scripts/embed_public_brief_into_html.mjs landing_page.html content.json
if (Test-Path market_pulse.json) {
  node scripts/embed_public_pulse_into_html.mjs landing_page.html market_pulse.json
}
if (Test-Path invest_vn_brief.json) {
  node scripts/embed_public_invest_vn_into_html.mjs landing_page.html invest_vn_brief.json
}

Write-Host "Done. Commit landing_page.html + content.json + gemini_digest_summary.json then push."
