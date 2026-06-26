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
            return {
                "games": SAMPLE_GAMES,
                "source": "sample",
                "note": "Off-season — showing sample data. 2026-27 season begins Oct 2026",
            }

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
        return {
            "games": SAMPLE_GAMES,
            "source": "sample",
            "note": "Off-season — showing sample data. 2026-27 season begins Oct 2026",
        }


SAMPLE_BOXSCORES: dict[str, list[dict]] = {
    "sample_001": [
        # Lakers (home)
        {"player_name": "LeBron James", "team": "LAL", "points": 28, "rebounds": 8, "assists": 9, "minutes": "36:24"},
        {"player_name": "Anthony Davis", "team": "LAL", "points": 22, "rebounds": 14, "assists": 2, "minutes": "34:10"},
        {"player_name": "Austin Reaves", "team": "LAL", "points": 18, "rebounds": 4, "assists": 5, "minutes": "31:00"},
        {"player_name": "D'Angelo Russell", "team": "LAL", "points": 14, "rebounds": 3, "assists": 7, "minutes": "28:45"},
        {"player_name": "Rui Hachimura", "team": "LAL", "points": 11, "rebounds": 5, "assists": 1, "minutes": "26:30"},
        {"player_name": "Taurean Prince", "team": "LAL", "points": 9, "rebounds": 3, "assists": 1, "minutes": "22:00"},
        {"player_name": "Jaxson Hayes", "team": "LAL", "points": 6, "rebounds": 4, "assists": 0, "minutes": "18:15"},
        # Warriors (away)
        {"player_name": "Stephen Curry", "team": "GSW", "points": 33, "rebounds": 5, "assists": 7, "minutes": "37:00"},
        {"player_name": "Andrew Wiggins", "team": "GSW", "points": 21, "rebounds": 6, "assists": 2, "minutes": "33:15"},
        {"player_name": "Draymond Green", "team": "GSW", "points": 8, "rebounds": 9, "assists": 11, "minutes": "32:00"},
        {"player_name": "Jonathan Kuminga", "team": "GSW", "points": 17, "rebounds": 4, "assists": 1, "minutes": "30:30"},
        {"player_name": "Brandin Podziemski", "team": "GSW", "points": 14, "rebounds": 5, "assists": 4, "minutes": "28:00"},
        {"player_name": "Moses Moody", "team": "GSW", "points": 11, "rebounds": 2, "assists": 1, "minutes": "24:45"},
        {"player_name": "Kevon Looney", "team": "GSW", "points": 5, "rebounds": 8, "assists": 2, "minutes": "20:00"},
    ],
    "sample_002": [
        # Celtics (home)
        {"player_name": "Jayson Tatum", "team": "BOS", "points": 31, "rebounds": 9, "assists": 5, "minutes": "37:30"},
        {"player_name": "Jaylen Brown", "team": "BOS", "points": 24, "rebounds": 6, "assists": 3, "minutes": "35:00"},
        {"player_name": "Jrue Holiday", "team": "BOS", "points": 14, "rebounds": 5, "assists": 8, "minutes": "32:15"},
        {"player_name": "Al Horford", "team": "BOS", "points": 10, "rebounds": 7, "assists": 2, "minutes": "28:00"},
        {"player_name": "Kristaps Porzingis", "team": "BOS", "points": 16, "rebounds": 5, "assists": 1, "minutes": "26:45"},
        {"player_name": "Payton Pritchard", "team": "BOS", "points": 12, "rebounds": 2, "assists": 4, "minutes": "24:00"},
        {"player_name": "Sam Hauser", "team": "BOS", "points": 9, "rebounds": 3, "assists": 1, "minutes": "20:30"},
        # Heat (away)
        {"player_name": "Bam Adebayo", "team": "MIA", "points": 22, "rebounds": 11, "assists": 4, "minutes": "36:00"},
        {"player_name": "Tyler Herro", "team": "MIA", "points": 26, "rebounds": 4, "assists": 6, "minutes": "34:30"},
        {"player_name": "Jimmy Butler", "team": "MIA", "points": 19, "rebounds": 6, "assists": 5, "minutes": "33:00"},
        {"player_name": "Kyle Lowry", "team": "MIA", "points": 8, "rebounds": 3, "assists": 7, "minutes": "28:00"},
        {"player_name": "Caleb Martin", "team": "MIA", "points": 11, "rebounds": 5, "assists": 1, "minutes": "25:15"},
        {"player_name": "Nikola Jovic", "team": "MIA", "points": 7, "rebounds": 4, "assists": 2, "minutes": "20:00"},
        {"player_name": "Haywood Highsmith", "team": "MIA", "points": 5, "rebounds": 3, "assists": 0, "minutes": "16:45"},
    ],
    "sample_003": [
        # Nuggets (home)
        {"player_name": "Nikola Jokic", "team": "DEN", "points": 29, "rebounds": 13, "assists": 10, "minutes": "35:00"},
        {"player_name": "Jamal Murray", "team": "DEN", "points": 22, "rebounds": 4, "assists": 7, "minutes": "33:30"},
        {"player_name": "Michael Porter Jr.", "team": "DEN", "points": 18, "rebounds": 7, "assists": 1, "minutes": "30:00"},
        {"player_name": "Aaron Gordon", "team": "DEN", "points": 12, "rebounds": 8, "assists": 3, "minutes": "28:15"},
        {"player_name": "Kentavious Caldwell-Pope", "team": "DEN", "points": 10, "rebounds": 2, "assists": 2, "minutes": "26:00"},
        {"player_name": "Reggie Jackson", "team": "DEN", "points": 8, "rebounds": 2, "assists": 4, "minutes": "20:00"},
        {"player_name": "Christian Braun", "team": "DEN", "points": 7, "rebounds": 3, "assists": 1, "minutes": "18:30"},
        # Suns (away)
        {"player_name": "Devin Booker", "team": "PHX", "points": 33, "rebounds": 4, "assists": 5, "minutes": "37:00"},
        {"player_name": "Kevin Durant", "team": "PHX", "points": 28, "rebounds": 8, "assists": 3, "minutes": "35:15"},
        {"player_name": "Bradley Beal", "team": "PHX", "points": 18, "rebounds": 3, "assists": 6, "minutes": "31:00"},
        {"player_name": "Jusuf Nurkic", "team": "PHX", "points": 11, "rebounds": 10, "assists": 2, "minutes": "27:00"},
        {"player_name": "Grayson Allen", "team": "PHX", "points": 14, "rebounds": 2, "assists": 1, "minutes": "24:30"},
        {"player_name": "Eric Gordon", "team": "PHX", "points": 9, "rebounds": 2, "assists": 2, "minutes": "20:00"},
        {"player_name": "Royce O'Neale", "team": "PHX", "points": 6, "rebounds": 4, "assists": 1, "minutes": "17:00"},
    ],
    "sample_004": [
        # Bucks (home)
        {"player_name": "Giannis Antetokounmpo", "team": "MIL", "points": 34, "rebounds": 12, "assists": 6, "minutes": "36:00"},
        {"player_name": "Damian Lillard", "team": "MIL", "points": 28, "rebounds": 3, "assists": 9, "minutes": "34:30"},
        {"player_name": "Khris Middleton", "team": "MIL", "points": 16, "rebounds": 5, "assists": 4, "minutes": "30:00"},
        {"player_name": "Brook Lopez", "team": "MIL", "points": 12, "rebounds": 6, "assists": 1, "minutes": "27:15"},
        {"player_name": "Bobby Portis", "team": "MIL", "points": 10, "rebounds": 8, "assists": 1, "minutes": "24:00"},
        {"player_name": "Pat Connaughton", "team": "MIL", "points": 8, "rebounds": 3, "assists": 2, "minutes": "20:30"},
        {"player_name": "Malik Beasley", "team": "MIL", "points": 6, "rebounds": 2, "assists": 1, "minutes": "16:45"},
        # 76ers (away)
        {"player_name": "Joel Embiid", "team": "PHI", "points": 32, "rebounds": 11, "assists": 4, "minutes": "35:30"},
        {"player_name": "Tyrese Maxey", "team": "PHI", "points": 26, "rebounds": 3, "assists": 8, "minutes": "34:00"},
        {"player_name": "Paul George", "team": "PHI", "points": 20, "rebounds": 6, "assists": 4, "minutes": "31:15"},
        {"player_name": "Tobias Harris", "team": "PHI", "points": 14, "rebounds": 7, "assists": 2, "minutes": "28:00"},
        {"player_name": "Kelly Oubre Jr.", "team": "PHI", "points": 11, "rebounds": 4, "assists": 1, "minutes": "25:30"},
        {"player_name": "De'Anthony Melton", "team": "PHI", "points": 7, "rebounds": 2, "assists": 3, "minutes": "20:00"},
        {"player_name": "Mo Bamba", "team": "PHI", "points": 5, "rebounds": 5, "assists": 0, "minutes": "14:00"},
    ],
}

_GENERIC_BOXSCORE = [
    {"player_name": "Player A", "team": "TM1", "points": 22, "rebounds": 6, "assists": 4, "minutes": "34:00"},
    {"player_name": "Player B", "team": "TM1", "points": 18, "rebounds": 4, "assists": 7, "minutes": "31:00"},
    {"player_name": "Player C", "team": "TM1", "points": 14, "rebounds": 8, "assists": 2, "minutes": "28:00"},
    {"player_name": "Player D", "team": "TM2", "points": 25, "rebounds": 5, "assists": 5, "minutes": "36:00"},
    {"player_name": "Player E", "team": "TM2", "points": 17, "rebounds": 3, "assists": 6, "minutes": "32:00"},
    {"player_name": "Player F", "team": "TM2", "points": 12, "rebounds": 7, "assists": 1, "minutes": "27:00"},
]


@app.get("/api/games/{game_id}/boxscore")
async def get_boxscore(game_id: str):
    if game_id.startswith("sample_"):
        players = SAMPLE_BOXSCORES.get(game_id, _GENERIC_BOXSCORE)
        return {"game_id": game_id, "players": players}

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


_STANDINGS_FALLBACK = {
    "season": "2025-26 Final Standings",
    "note": "2026-27 season begins October 2026",
    "east": [
        {"team_name": "Cleveland Cavaliers",    "wins": 64, "losses": 18, "win_pct": 0.780, "conference": "East", "rank": 1},
        {"team_name": "Boston Celtics",         "wins": 61, "losses": 21, "win_pct": 0.744, "conference": "East", "rank": 2},
        {"team_name": "New York Knicks",        "wins": 51, "losses": 31, "win_pct": 0.622, "conference": "East", "rank": 3},
        {"team_name": "Indiana Pacers",         "wins": 50, "losses": 32, "win_pct": 0.610, "conference": "East", "rank": 4},
        {"team_name": "Milwaukee Bucks",        "wins": 49, "losses": 33, "win_pct": 0.598, "conference": "East", "rank": 5},
        {"team_name": "Philadelphia 76ers",     "wins": 47, "losses": 35, "win_pct": 0.573, "conference": "East", "rank": 6},
        {"team_name": "Miami Heat",             "wins": 46, "losses": 36, "win_pct": 0.561, "conference": "East", "rank": 7},
        {"team_name": "Chicago Bulls",          "wins": 39, "losses": 43, "win_pct": 0.476, "conference": "East", "rank": 8},
    ],
    "west": [
        {"team_name": "Oklahoma City Thunder",  "wins": 68, "losses": 14, "win_pct": 0.829, "conference": "West", "rank": 1},
        {"team_name": "Houston Rockets",        "wins": 52, "losses": 30, "win_pct": 0.634, "conference": "West", "rank": 2},
        {"team_name": "Los Angeles Lakers",     "wins": 50, "losses": 32, "win_pct": 0.610, "conference": "West", "rank": 3},
        {"team_name": "Golden State Warriors",  "wins": 48, "losses": 34, "win_pct": 0.585, "conference": "West", "rank": 4},
        {"team_name": "Denver Nuggets",         "wins": 45, "losses": 37, "win_pct": 0.549, "conference": "West", "rank": 5},
        {"team_name": "Dallas Mavericks",       "wins": 39, "losses": 43, "win_pct": 0.476, "conference": "West", "rank": 6},
        {"team_name": "Memphis Grizzlies",      "wins": 41, "losses": 41, "win_pct": 0.500, "conference": "West", "rank": 7},
        {"team_name": "Sacramento Kings",       "wins": 40, "losses": 42, "win_pct": 0.488, "conference": "West", "rank": 8},
    ],
}


@app.get("/api/standings")
@cached(ttl_seconds=3600)
async def get_standings():
    try:
        from nba_api.stats.endpoints import leaguestandings

        ls = leaguestandings.LeagueStandings()
        df = ls.get_data_frames()[0]

        if df.empty:
            print("Standings DataFrame is empty — returning fallback")
            return _STANDINGS_FALLBACK

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
        )[:8]
        west = sorted(
            [s for s in standings if s["conference"].lower() == "west"],
            key=lambda x: x["rank"],
        )[:8]

        if not east and not west:
            print("Standings parsing yielded no results — returning fallback")
            return _STANDINGS_FALLBACK

        return {"season": None, "note": None, "east": east, "west": west}

    except Exception as e:
        print(f"Error fetching standings: {e}")
        return _STANDINGS_FALLBACK
