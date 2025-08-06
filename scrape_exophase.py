import csv
import sys
import json
from typing import Iterable, Dict, Any
import time

try:
    # Python 3.11+
    from importlib.resources import files as _files  # noqa: F401
except Exception:  # pragma: no cover
    pass

import urllib.request
import urllib.error

BASE_URL = (
    "https://api.exophase.com/public/player/4972201/games?environment=nintendo&sort=5&showHidden=0&me=744281&query="
)


def fetch_json(url: str) -> Dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            # Identify politely; many endpoints require a UA header
            "User-Agent": "switch-game-tracking-scraper/1.0 (+https://exophase.com)"
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            data = resp.read().decode(charset, errors="replace")
            return json.loads(data)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP error {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        raise SystemExit(f"Network error: {e.reason}")
    except json.JSONDecodeError as e:
        raise SystemExit(f"Invalid JSON: {e}")


def iter_games(payload: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    # The example shows the top-level shape: {"success": true, "games": [ ... ]}
    games = payload.get("games")
    if not isinstance(games, list):
        return []
    return games


def extract_row(game: Dict[str, Any]) -> Dict[str, str]:
    # Title appears in game["meta"]["title"] per the sample
    meta = game.get("meta") or {}
    title = meta.get("title") or ""

    playtime = game.get("playtime") or ""

    image = game.get("resource_standard") or ""

    last_played = game.get("lastplayed_utc") or ""

    return {
        "title": str(title),
        "playtime": str(playtime),
        "image_url": str(image),
        "last_played": str(last_played),
    }


def write_csv(rows: Iterable[Dict[str, str]], out_path: str) -> None:
    fieldnames = ["title", "playtime", "image_url", "last_played"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def build_url(page: int) -> str:
    return f"{BASE_URL}&page={page}"


def main(argv: list[str]) -> int:
    import os
    repo_root = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(repo_root, "games.csv")
    if len(argv) > 1:
        user_path = argv[1]
        out_path = user_path if os.path.isabs(user_path) else os.path.join(repo_root, user_path)

    all_rows: list[Dict[str, str]] = []
    page = 1
    while True:
        print(f"Fetching page {page}...")
        payload = fetch_json(build_url(page))
        games = list(iter_games(payload))
        if not games:
            break
        all_rows.extend(extract_row(g) for g in games)
        page += 1
        # add a small delay to avoid hitting the server too hard
        time.sleep(5)

    write_csv(all_rows, out_path)
    print(f"Wrote {len(all_rows)} rows to {out_path} across {page-1} page(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
