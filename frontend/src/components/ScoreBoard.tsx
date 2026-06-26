import type { Game } from "../types";
import GameCard from "./GameCard";
import LoadingSpinner from "./LoadingSpinner";

interface Props {
  games: Game[];
  loading: boolean;
  lastUpdated: Date | null;
}

const SAMPLE_GAMES: Game[] = [
  {
    game_id: "sample_001",
    home_team: "Los Angeles Lakers",
    away_team: "Golden State Warriors",
    home_score: 108,
    away_score: 115,
    game_status: "Final",
    period: 4,
    arena: "Crypto.com Arena",
    city: "Los Angeles",
  },
  {
    game_id: "sample_002",
    home_team: "Boston Celtics",
    away_team: "Miami Heat",
    home_score: 97,
    away_score: 89,
    game_status: "Final",
    period: 4,
    arena: "TD Garden",
    city: "Boston",
  },
  {
    game_id: "sample_003",
    home_team: "Denver Nuggets",
    away_team: "Phoenix Suns",
    home_score: 0,
    away_score: 0,
    game_status: "Scheduled",
    period: 0,
    arena: "Ball Arena",
    city: "Denver",
  },
  {
    game_id: "sample_004",
    home_team: "Milwaukee Bucks",
    away_team: "Philadelphia 76ers",
    home_score: 62,
    away_score: 58,
    game_status: "Live",
    game_clock: "4:32",
    period: 3,
    arena: "Fiserv Forum",
    city: "Milwaukee",
  },
];

export default function ScoreBoard({ games, loading, lastUpdated }: Props) {
  if (loading && games.length === 0) {
    return <LoadingSpinner />;
  }

  const isFallback = games.length === 0;
  const displayGames = isFallback ? SAMPLE_GAMES : games;

  return (
    <section>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-500">
          Today's Games
        </h2>
        {lastUpdated && !isFallback && (
          <span className="text-xs text-gray-600">
            Updated {lastUpdated.toLocaleTimeString()}
          </span>
        )}
      </div>

      {isFallback && (
        <div className="mb-4 rounded-lg bg-amber-500/10 px-4 py-2 text-center text-xs text-amber-500/70">
          🏀 Off-season — showing sample games · Live data returns Oct 2026
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {displayGames.map((game) => (
          <GameCard key={game.game_id} game={game} />
        ))}
      </div>
    </section>
  );
}
