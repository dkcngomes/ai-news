# AI News — latest AI headlines (GitHub Pages + Actions)

Zero-dependency Python project that scrapes AI news from RSS/Atom feeds
and serves them as a static site, fully automated and **$0/month**.

The frontend is a live-feeling newsroom UI: dark/light mode, a scrolling
TV-style ticker, an animated "scraping" status, and fresh-article badges.

## How it works

1. **GitHub Actions** runs `scraper.py` every hour (`.github/workflows/scrape.yml`)
2. The scraper fetches 5 AI news feeds → dedupes → sorts → writes `news.json`
3. The commit-back step pushes updated `news.json` to `main`
4. **GitHub Pages** serves `index.html` + `news.json` from the repo root

## Features

- **Dark / light mode toggle** — 🌙/☀️ button in the header; remembers your
  choice in `localStorage` and falls back to your system preference
  (`prefers-color-scheme`), applied before first paint to avoid a flash
- **TV-style news ticker** — headlines scroll continuously under the header
  at a steady pace (pauses are not a thing here — it always moves), with
  soft edge fades; hover no longer freezes it
- **"Actively scraping" feel** — on load, a spinning radar + cycling status
  messages ("Connecting to sources…", "Fetching RSS feeds…", "Parsing
  headlines…") with shimmer skeleton cards, then cards stagger in
- **Live countdown** — "⏳ next scrape in m:ss" shows when the page will
  auto-refresh (every 5 minutes)
- **NEW badges** — articles younger than 1 hour get a pulsing green badge
- **Pulsing LIVE indicator** — green dot in the header signals the feed is live
- **Accessible** — respects `prefers-reduced-motion`

## Files

| File                          | Purpose                                              |
|-------------------------------|------------------------------------------------------|
| `scraper.py`                  | Fetches feeds, parses RSS/Atom, dedupes, sorts       |
| `index.html`                  | Static frontend (card grid, search, source filter, theme toggle, ticker, animations) |
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
