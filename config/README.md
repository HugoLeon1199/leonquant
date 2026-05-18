# Crawl configuration (tiered)

Leon Quant mirrors the **two-layer** idea from `leon_web_intel`:

| File | Role |
|------|------|
| **`sources_seed.txt`** | Tier headers (`# …`) + **homepage / section URLs** — scope & taxonomy only; **not** read directly by `crawl_financial_news.py`. |
| **`news_sources_tiered.json`** | Same tiers as structured JSON; each item **`url` must be an RSS/Atom feed** used by the crawler. |
| **`news_sources.json`** | Legacy flat list `{ "sources": [ … ] }`; unchanged default unless you pass `--sources`. |

## Run with tiers

```powershell
python crawl_financial_news.py --sources config/news_sources_tiered.json --per-source-limit 0 --max-total 0
```

Articles in `news_output.json` include optional fields **`tier`** and **`tier_title`** when using the tiered file.

## Adding a site from `sources_seed.txt`

1. Find a working RSS URL for that domain (browser “view source” / `/rss` patterns).
2. Add an object under the right `tier` in **`news_sources_tiered.json`** with `name`, `url`, `category`, `region`.
3. Optionally run `python scripts/validate_news_sources_tiered.py`.
