# Financial News Crawler

This MVP collects public finance/crypto RSS feeds and writes a clean JSON file for the next AI summarization step.

## Files

- `news_sources.json` - RSS sources and categories (flat `{ "sources": [...] }`).
- `config/news_sources_tiered.json` - Same feeds grouped by **tier** (aligned with `config/sources_seed.txt` taxonomy); use `--sources config/news_sources_tiered.json`. Each article gains optional `tier` / `tier_title`.
- `config/sources_seed.txt` - Homepage/section URLs per tier (reference only; crawler still needs RSS URLs in JSON).
- `scripts/build_news_sources_tiered.py` - Regenerate tiered JSON from `news_sources.json` + extras.
- `crawl_financial_news.py` - crawler script.
- `news_output.json` - raw normalized output for AI/API processing.
- `content.json` - optional website fallback output when running with `--update-content`.

## Run

```powershell
& "D:\save code\PythonProject\.venv\Scripts\python.exe" "D:\save code\PythonProject\crawl_financial_news.py" --update-content
```

## Output shape

```json
{
  "generated_at": "2026-05-09T18:00:00+00:00",
  "count": 50,
  "articles": [
    {
      "title": "Headline",
      "url": "https://example.com/news",
      "summary": "Short article summary",
      "published_at": "2026-05-09T12:00:00+00:00",
      "source": "CNBC Markets",
      "category": "markets"
    }
  ],
  "errors": []
}
```

## Next step

Send `news_output.json` to the AI summarizer pipeline:

1. Filter and rank important articles.
2. Group by theme: macro, stocks, crypto, rates, commodities.
3. Ask Gemini/GPT/Grok to summarize using the same JSON schema.
4. Use a judge/consensus step to produce the final daily briefing.
