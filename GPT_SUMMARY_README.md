# GPT News Summarizer

This script reads `news_output.json`, sends selected news items to OpenAI GPT, and writes:

- `gpt_summary.json` - structured AI summary for later pipelines.
- `content.json` - website cards when `--update-content` is used.

## 1) Configure API key

Copy `.env.example` to `.env` and replace the placeholder:

```powershell
Copy-Item ".env.example" ".env"
```

`.env`:

```env
OPENAI_API_KEY=your-real-key
OPENAI_MODEL=gpt-4o-mini
```

Do not share or commit `.env`.

## 2) Dry run

```powershell
$env:PYTHONIOENCODING='utf-8'; & "D:\save code\PythonProject\.venv\Scripts\python.exe" "D:\save code\PythonProject\summarize_news_gpt.py" --dry-run --max-articles 80
```

## 3) Call GPT and update website

```powershell
$env:PYTHONIOENCODING='utf-8'; & "D:\save code\PythonProject\.venv\Scripts\python.exe" "D:\save code\PythonProject\summarize_news_gpt.py" --max-articles 80 --update-content
```

Then refresh:

```text
http://localhost:5600
```

## Notes

- `--max-articles` controls cost. Start with 50-80.
- The script asks GPT to return strict JSON.
- The website displays `content.json`, so `--update-content` publishes the summary locally.
