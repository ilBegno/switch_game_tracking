# Switch Game Tracking

A lightweight web viewer for Nintendo Switch play history, with data scraped from Exophase and published via GitHub Pages.

## Repository Layout

- `docs/`
  - `index.html` – Web UI (fetches `games.json`)
  - `games.json` – Scraped data published to Pages
  - `logo.svg`, `robots.txt` – Assets and robots policy
- `scrape_exophase.py` – Python scraper for Exophase (outputs to `docs/games.json` by default)
- `serve_games.py` – Local dev static server (serves `docs/`)
- `.github/workflows/scrape.yml` – Nightly job to refresh `docs/games.json`

## Usage

### Local development

1. Ensure you have Python 3 installed.
2. Run the local server:
   ```bash
   python serve_games.py
   ```
3. Your browser should open to `http://localhost:8000/` (serving `docs/`).


## Automated Updates

A GitHub Actions workflow updates the data nightly:

1. `scrape_exophase.py` runs daily at 04:23 UTC to fetch the latest game data.
2. The workflow commits the updated `docs/games.json` to the repository.

## Features

- Search by title
- Sort by recently played, playtime, or alphabetically
- Responsive, dark-themed UI
- Auto-updating data via GitHub Actions
