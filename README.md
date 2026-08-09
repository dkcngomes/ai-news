# AI News — latest AI headlines (GitHub Pages + Actions)

Zero-dependency Python project that scrapes AI news from RSS/Atom feeds
and serves them as a static site, fully automated and **$0/month**.

## How it works

1. **GitHub Actions** runs `scraper.py` every hour (`.github/workflows/scrape.yml`)
2. The scraper fetches 5 AI news feeds → dedupes → sorts → writes `news.json`
3. The commit-back step pushes updated `news.json` to `main`
4. **GitHub Pages** serves `index.html` + `news.json` from the repo root

## Files

| File                          | Purpose                                              |
|-------------------------------|------------------------------------------------------|
| `scraper.py`                  | Fetches feeds, parses RSS/Atom, dedupes, sorts       |
| `index.html`                  | Static frontend (card grid, search, source filter)   |
| `.github/workflows/scrape.yml`| Hourly scrape + commit-back automation               |
| `news.json`                   | Generated data (committed so Pages can serve it)     |

## Deploying (one-time setup)

1. Create a **new empty GitHub repo** (e.g. `ai-news`)
2. Push this folder to it (default branch must be `main`)
3. Repo **Settings → Pages → Build and deployment → Source: Deploy from a branch → main / (root)** → Save
4. Site is live at `https://<your-username>.github.io/<repo-name>/`
5. Optional: trigger a manual scrape from the **Actions** tab (workflow_dispatch)

## Local development

```bash
python scraper.py          # regenerate news.json
python -m http.server 8000 # serve the static site, open http://localhost:8000
```

`server.py` (the old local web server with `/api/news` + `/api/refresh`)
is no longer used for hosting; it's kept for local API-style previews.

## Sources

- TechCrunch AI
- The Verge AI
- VentureBeat AI
- Wired AI
- Hacker News (AI keyword)

## Notes

- `scraper.py` uses an unverified SSL context because the system cert
  store on this (Windows) dev machine fails verification. On GitHub's
  Ubuntu runners the cert store is healthy; the code path works either way.
- Hourly schedule = ~1,440 Actions minutes/month, well inside the free
  tier (2,000 min/month private / unlimited public repos).
- Feed data is public news — fine for public hosting.
