# Realtime Content Architecture (Production)

## Recommended stack

- Frontend: Next.js on Vercel
- Database + realtime: Supabase (Postgres + Realtime)
- Automation: n8n (or Make) + Gmail trigger
- AI generation: OpenAI API (server side only)
- Code repo: GitHub

## Why this is better than GPT -> GitHub direct

- Realtime updates without rebuilding site each content change
- Better security (no secret keys on client)
- Easier moderation and rollback (status draft/published)
- Cleaner separation: code in GitHub, content in database

## Data model (minimum)

Table: `posts`

- `id` (uuid, primary key)
- `title` (text)
- `content` (text)
- `source` (text) // gmail, manual, api
- `status` (text) // draft, published
- `created_at` (timestamp)
- `published_at` (timestamp, nullable)

## End-to-end flow

1) New Gmail arrives (ChatGPT result)
2) n8n workflow reads email body
3) Optional cleanup/summarize with OpenAI
4) Insert/Update row in Supabase `posts`
5) Frontend fetches published posts via Supabase API
6) Supabase Realtime pushes changes to clients instantly

## Security rules

- Use Supabase service role key only in n8n/server
- Frontend uses anon key with RLS policy (read only published posts)
- Never expose OpenAI key in frontend

## Phase rollout

### Phase 1 (quick launch)
- Keep current static site
- Add API fetch to published posts endpoint
- Manual publish from Supabase table

### Phase 2 (semi-automation)
- Gmail -> n8n -> Supabase draft
- Review then mark `published`

### Phase 3 (full automation)
- Gmail -> OpenAI cleanup -> auto publish rule
- Realtime widget + notification on new post

## Minimal API contract (frontend expects)

```json
{
  "chatSectionTitle": "Noi dung GPT moi nhat",
  "chatItems": [
    {
      "title": "Ban tin 01",
      "content": "Noi dung...",
      "createdAt": "2026-05-09T17:00:00Z"
    }
  ]
}
```

## What to build next in this project

1) Add a small backend endpoint (`/api/feed`) to map Supabase rows to the JSON contract above.
2) Update `landing_page.html` fetch priority:
   - `/api/feed` -> Apps Script URL -> `content.json` fallback.
3) Add admin toggle in DB (`status=published`) for safe content control.

## Estimated effort

- MVP (Supabase + fetch + publish control): 0.5-1 day
- Add n8n Gmail ingestion: +0.5 day
- Add OpenAI auto-clean + moderation: +0.5 day
