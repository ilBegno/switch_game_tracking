# Switch Game Tracking

A web application to track and view Nintendo Switch game playtime data scraped from Exophase.

## Files

- `scrape_exophase.py` - Python script that scrapes game data from Exophase
- `games.json` - Raw game data in JSON format
- `games_viewer.html` - Web interface that fetches data from games.json (requires local server due to CORS)
- `games_viewer_embedded.html` - **Standalone web interface with embedded JSON data (no CORS issues)**
- `embed_json.py` - Script that creates the embedded HTML file from the original HTML and JSON
- `serve_games.py` - Local development server

## Usage

### View Games (Recommended)

Open `games_viewer_embedded.html` directly in your browser. This file contains all the game data embedded within it, so it works without needing a local server or dealing with CORS issues.

### View Games (Alternative)

If you prefer using the original HTML file that fetches JSON dynamically:

1. Run the local server: `python serve_games.py`
2. Open `http://localhost:8000` in your browser

## Automated Updates

The repository uses GitHub Actions to automatically update the game data nightly:

1. `scrape_exophase.py` runs daily at 04:23 UTC to fetch latest game data
2. `embed_json.py` runs to create an updated embedded HTML file  
3. Both `games.json` and `games_viewer_embedded.html` are committed to the repository

## Features

- Search games by title
- Sort by recently played, playtime, or alphabetically
- Responsive design with dark theme
- No external dependencies (embedded version)
- Auto-updating via GitHub Actions

## Development

To manually update the embedded HTML file after modifying the JSON data:

```bash
python embed_json.py
```

This will create/update `games_viewer_embedded.html` with the latest data from `games.json`.
