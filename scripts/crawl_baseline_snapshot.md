# Crawl baseline snapshot

- generated_at_utc: 2026-05-19T07:39:59.907864+00:00
- db: `D:\save code\WEB\Economy\leonquant\data\web_intel_leonquant.duckdb`
- calendar_anchor (Asia/Ho_Chi_Minh): **2026-05-19**
- recent_calendar_days: 2 (from crawl_rules.yaml)

## Articles
- articles_total: **5129**
- distinct_source_id: **62**
- news_output_today.json count: **2398**

## crawl_errors
- total: **11290**

| error_type | n |
| --- | ---: |
| NotToday | 7000 |
| AccessControlDetected | 3251 |
| ShortContent | 399 |
| FetchError | 356 |
| HttpError | 256 |
| ConnectError | 17 |
| ConnectTimeout | 9 |
| ReadTimeout | 2 |

## Profiles / skip
- source_profiles: 99
- source_crawl_skip: 18

## Commands
```bash
python scripts/crawl_error_snapshot.py
python scripts/investigate_zero_article_sources.py
python scripts/source_coverage_report.py
```
