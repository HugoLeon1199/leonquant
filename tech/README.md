# LeonQuant Tech 72h

This folder contains the active Technology and AI pipeline.

- Window: latest 72 hours.
- Frequency: once every 3 days.
- Sources: web categories and forum RSS that pass validation.
- GDELT: 72-hour partitioned query with dry-run and maximum-bytes guard.
- Secrets: reuses `GEMINI_API_KEY`, `GCP_SA_JSON`, and `GOOGLE_CLOUD_PROJECT`; no new key is required.
- Public output: `tech/data/publication.json`, rendered by `tech/index.html`.

Run order:

```bash
python tech/validate_sources.py --resume
python tech/crawl.py
python tech/gdelt.py --dry-run
python tech/gdelt.py
python tech/publication.py
python tech/validate_publication.py
python tech/test_pipeline.py
```

The workflows must remain under `.github/workflows/` because GitHub Actions only loads workflow files from that directory.
