# Leon Web Intel (gọn cho Leon Quant)

**Entry:** `run_profile.py` → `run_scrapy.py`. **Output dùng downstream:** DuckDB → `scripts/export_news_full_for_ai.py` → `news_for_ai_clean.json` (digest).

**Chạy (từ root `leonquant`):**

```powershell
pip install -r leon_web_intel/requirements.txt
playwright install
python scripts/run_intel_full_daily.py --date today --timezone Asia/Ho_Chi_Minh
```

**Cấu hình crawl:** `leon_web_intel/config/crawl_rules.yaml`. **Nguồn & tier:** `leonquant/config/sources_seed.txt`, `leonquant/config/tiers/*.txt`, `tiers_manifest.json`.
