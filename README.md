# NBA Live Tracker

Real-time NBA game scores and standings — FastAPI backend, React frontend.

## Live

| | URL |
|-|-----|
| Frontend | https://nba-live-tracker-mauve.vercel.app |
| Backend API | https://nba-live-tracker-api.onrender.com |

## Stack

| Layer    | Tech                                      |
|----------|-------------------------------------------|
| Backend  | Python · FastAPI · nba-api · Render       |
| Frontend | React · TypeScript · Vite · Tailwind CSS · Vercel |

## Features

- Live scores with auto-refresh every 30 seconds
- Game status badges (Live / Final / Scheduled)
- Click any completed/live game to view the box score
- Eastern & Western Conference standings sidebar
- Graceful fallback to sample data when no games are scheduled
- Responsive layout: 2-column desktop, 1-column mobile

## Local Development

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API available at `http://localhost:8000`

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Health check |
| `GET /api/games/today` | Today's games |
| `GET /api/games/{id}/boxscore` | Game box score |
| `GET /api/standings` | Conference standings |

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`

## Deployment

| Service | URL |
|---------|-----|
| Backend | https://nba-live-tracker-api.onrender.com |
| Frontend | https://nba-live-tracker-mauve.vercel.app |

Backend is deployed on Render (root dir: `backend/`), frontend on Vercel (root dir: `frontend/`).
