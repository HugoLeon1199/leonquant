# Leon Web Intel (gọn cho Leon Quant)

**Entry:** `run_profile.py` → `run_scrapy.py`. **Output dùng downstream:** DuckDB rồi `leonquant/scripts/export_intel_to_news_output.py` → `news_output.json`.

**Chạy (từ root `leonquant`):**

```powershell
pip install -r leon_web_intel/requirements.txt
playwright install
python scripts/run_intel_full_daily.py --date today --timezone Asia/Ho_Chi_Minh
```

**Cấu hình crawl:** `leon_web_intel/config/crawl_rules.yaml`. **Nguồn & tier:** `leonquant/config/sources_seed.txt`, `leonquant/config/tiers/*.txt`, `tiers_manifest.json`.
