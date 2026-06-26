import time
import os
from datetime import datetime, timedelta
from functools import wraps
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="NBA Live Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://nba-live-tracker.vercel.app",
        "https://*.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "name": "NBA Live Tracker API",
        "version": "1.0.0",
        "endpoints": [
            "/api/health",
            "/api/games/today",
            "/api/games/{game_id}/boxscore",
            "/api/standings",
        ],
    }

# Simple in-memory cache: {key: (value, expires_at)}
_cache: dict[str, tuple[Any, float]] = {}


def cached(ttl_seconds: int):
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            key = fn.__name__
            now = time.time()
            if key in _cache:
                value, expires_at = _cache[key]
                if now < expires_at:
                    return value
            result = await fn(*args, **kwargs)
            _cache[key] = (result, now + ttl_seconds)
            return result
        return wrapper
    return decorator


SAMPLE_GAMES = [
    {
        "game_id": "sample_001",
        "home_team": "Los Angeles Lakers",
        "away_team": "Golden State Warriors",
        "home_score": 108,
        "away_score": 115,
        "game_status": "Final",
        "game_clock": None,
        "period": 4,
        "arena": "Crypto.com Arena",
        "city": "Los Angeles",
    },
    {
        "game_id": "sample_002",
        "home_team": "Boston Celtics",
        "away_team": "Miami Heat",
        "home_score": 97,
        "away_score": 89,
        "game_status": "Final",
        "game_clock": None,
        "period": 4,
        "arena": "TD Garden",
        "city": "Boston",
    },
    {
        "game_id": "sample_003",
        "home_team": "Denver Nuggets",
        "away_team": "Phoenix Suns",
        "home_score": 0,
        "away_score": 0,
        "game_status": "Scheduled",
        "game_clock": None,
        "period": 0,
        "arena": "Ball Arena",
        "city": "Denver",
    },
    {
        "game_id": "sample_004",
        "home_team": "Milwaukee Bucks",
        "away_team": "Philadelphia 76ers",
        "home_score": 62,
        "away_score": 58,
        "game_status": "Live",
        "game_clock": "4:32",
        "period": 3,
        "arena": "Fiserv Forum",
        "city": "Milwaukee",
    },
]


def _parse_game_status(status_text: str) -> str:
    s = (status_text or "").strip().lower()
    if "halftime" in s or "qtr" in s or "half" in s:
        return "Live"
    if s in ("", "1", "1st qtr", "2nd qtr", "3rd qtr", "4th qtr"):
        return "Live"
    if "final" in s:
        return "Final"
    if "pm" in s or "am" in s or "et" in s:
        return "Scheduled"
    # nba_api uses numeric codes: 1=scheduled, 2=live, 3=final
    if status_text.strip() == "3":
        return "Final"
    if status_text.strip() == "2":
        return "Live"
    return "Scheduled"


@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/games/today")
@cached(ttl_seconds=30)
async def get_today_games():
    try:
        from nba_api.live.nba.endpoints import scoreboard as live_scoreboard

        sb = live_scoreboard.ScoreBoard()
        data = sb.get_dict()

        games_raw = data.get("scoreboard", {}).get("games", [])
        if not games_raw:
            print("No live games found — returning sample data")
            return {"games": SAMPLE_GAMES, "source": "sample"}

        games = []
        for g in games_raw:
            home = g.get("homeTeam", {})
            away = g.get("awayTeam", {})

            status_text = g.get("gameStatusText", "")
            status_num = g.get("gameStatus", 1)

            if status_num == 3:
                game_status = "Final"
            elif status_num == 2:
                game_status = "Live"
            else:
                game_status = "Scheduled"

            clock = g.get("gameClock", "")
            if clock and clock.startswith("PT"):
                # ISO 8601 duration e.g. PT04M32.00S → "4:32"
                try:
                    import re
                    m = re.match(r"PT(\d+)M([\d.]+)S", clock)
                    if m:
                        mins = int(m.group(1))
                        secs = int(float(m.group(2)))
                        clock = f"{mins}:{secs:02d}"
                except Exception:
                    pass

            games.append(
                {
                    "game_id": g.get("gameId", ""),
                    "home_team": home.get("teamName", ""),
                    "away_team": away.get("teamName", ""),
                    "home_score": home.get("score", 0),
                    "away_score": away.get("score", 0),
                    "game_status": game_status,
                    "game_clock": clock if game_status == "Live" else None,
                    "period": g.get("period", 0),
                    "arena": g.get("arenaName", ""),
                    "city": g.get("arenaCity", ""),
                }
            )

        return {"games": games, "source": "live"}

    except Exception as e:
        print(f"Error fetching today's games: {e}")
        return {"games": SAMPLE_GAMES, "source": "sample"}


@app.get("/api/games/{game_id}/boxscore")
async def get_boxscore(game_id: str):
    if game_id.startswith("sample_"):
        return {
            "game_id": game_id,
            "players": [
                {"player_name": "LeBron James", "team": "LAL", "points": 28, "rebounds": 8, "assists": 9, "minutes": "36:24"},
                {"player_name": "Anthony Davis", "team": "LAL", "points": 22, "rebounds": 14, "assists": 2, "minutes": "34:10"},
                {"player_name": "Austin Reaves", "team": "LAL", "points": 18, "rebounds": 4, "assists": 5, "minutes": "31:00"},
                {"player_name": "D'Angelo Russell", "team": "LAL", "points": 14, "rebounds": 3, "assists": 7, "minutes": "28:45"},
                {"player_name": "Rui Hachimura", "team": "LAL", "points": 11, "rebounds": 5, "assists": 1, "minutes": "26:30"},
                {"player_name": "Stephen Curry", "team": "GSW", "points": 33, "rebounds": 5, "assists": 7, "minutes": "37:00"},
                {"player_name": "Klay Thompson", "team": "GSW", "points": 21, "rebounds": 3, "assists": 2, "minutes": "33:15"},
                {"player_name": "Draymond Green", "team": "GSW", "points": 8, "rebounds": 9, "assists": 11, "minutes": "32:00"},
                {"player_name": "Andrew Wiggins", "team": "GSW", "points": 17, "rebounds": 6, "assists": 2, "minutes": "30:30"},
                {"player_name": "Jonathan Kuminga", "team": "GSW", "points": 14, "rebounds": 4, "assists": 1, "minutes": "27:00"},
            ],
        }

    try:
        from nba_api.live.nba.endpoints import boxscore as live_boxscore

        bs = live_boxscore.BoxScore(game_id=game_id)
        data = bs.get_dict()

        all_players = []
        for team_key in ("homeTeam", "awayTeam"):
            team_data = data.get("game", {}).get(team_key, {})
            team_abbr = team_data.get("teamTricode", "")
            for p in team_data.get("players", []):
                stats = p.get("statistics", {})
                minutes_raw = stats.get("minutesCalculated", "PT00M00.00S")
                try:
                    import re
                    m = re.match(r"PT(\d+)M([\d.]+)S", minutes_raw)
                    minutes = f"{int(m.group(1))}:{int(float(m.group(2))):02d}" if m else "0:00"
                except Exception:
                    minutes = "0:00"

                all_players.append(
                    {
                        "player_name": p.get("name", ""),
                        "team": team_abbr,
                        "points": stats.get("points", 0),
                        "rebounds": stats.get("reboundsTotal", 0),
                        "assists": stats.get("assists", 0),
                        "minutes": minutes,
                        "_minutes_raw": int(minutes.split(":")[0]) if ":" in minutes else 0,
                    }
                )

        all_players.sort(key=lambda x: x["_minutes_raw"], reverse=True)

        home_abbr = data.get("game", {}).get("homeTeam", {}).get("teamTricode", "")
        away_abbr = data.get("game", {}).get("awayTeam", {}).get("teamTricode", "")

        home_players = [p for p in all_players if p["team"] == home_abbr][:5]
        away_players = [p for p in all_players if p["team"] == away_abbr][:5]

        for p in home_players + away_players:
            del p["_minutes_raw"]

        return {"game_id": game_id, "players": home_players + away_players}

    except Exception as e:
        print(f"Error fetching boxscore for {game_id}: {e}")
        return {"game_id": game_id, "players": []}


@app.get("/api/standings")
@cached(ttl_seconds=3600)
async def get_standings():
    try:
        from nba_api.stats.endpoints import leaguestandings

        ls = leaguestandings.LeagueStandings()
        df = ls.get_data_frames()[0]

        standings = []
        for _, row in df.iterrows():
            standings.append(
                {
                    "team_name": row.get("TeamName", ""),
                    "wins": int(row.get("WINS", 0)),
                    "losses": int(row.get("LOSSES", 0)),
                    "win_pct": float(row.get("WinPCT", 0.0)),
                    "conference": row.get("Conference", ""),
                    "rank": int(row.get("PlayoffRank", 0)),
                }
            )

        east = sorted(
            [s for s in standings if s["conference"].lower() == "east"],
            key=lambda x: x["rank"],
        )[:5]
        west = sorted(
            [s for s in standings if s["conference"].lower() == "west"],
            key=lambda x: x["rank"],
        )[:5]

        return {"east": east, "west": west}

    except Exception as e:
        print(f"Error fetching standings: {e}")
        return {
            "east": [
                {"team_name": "Boston Celtics", "wins": 61, "losses": 21, "win_pct": 0.744, "conference": "East", "rank": 1},
                {"team_name": "Milwaukee Bucks", "wins": 49, "losses": 33, "win_pct": 0.598, "conference": "East", "rank": 2},
                {"team_name": "Philadelphia 76ers", "wins": 47, "losses": 35, "win_pct": 0.573, "conference": "East", "rank": 3},
                {"team_name": "Cleveland Cavaliers", "wins": 48, "losses": 34, "win_pct": 0.585, "conference": "East", "rank": 4},
                {"team_name": "New York Knicks", "wins": 47, "losses": 35, "win_pct": 0.573, "conference": "East", "rank": 5},
            ],
            "west": [
                {"team_name": "Oklahoma City Thunder", "wins": 57, "losses": 25, "win_pct": 0.695, "conference": "West", "rank": 1},
                {"team_name": "Denver Nuggets", "wins": 54, "losses": 28, "win_pct": 0.659, "conference": "West", "rank": 2},
                {"team_name": "Minnesota Timberwolves", "wins": 56, "losses": 26, "win_pct": 0.683, "conference": "West", "rank": 3},
                {"team_name": "Los Angeles Clippers", "wins": 51, "losses": 31, "win_pct": 0.622, "conference": "West", "rank": 4},
                {"team_name": "Dallas Mavericks", "wins": 50, "losses": 32, "win_pct": 0.610, "conference": "West", "rank": 5},
            ],
        }
