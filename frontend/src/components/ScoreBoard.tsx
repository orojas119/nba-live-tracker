import type { Game } from "../types";
import GameCard from "./GameCard";
import LoadingSpinner from "./LoadingSpinner";

interface Props {
  games: Game[];
  loading: boolean;
  lastUpdated: Date | null;
}

export default function ScoreBoard({ games, loading, lastUpdated }: Props) {
  if (loading && games.length === 0) {
    return <LoadingSpinner />;
  }

  return (
    <section>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-500">
          Today's Games
        </h2>
        {lastUpdated && (
          <span className="text-xs text-gray-600">
            Updated {lastUpdated.toLocaleTimeString()}
          </span>
        )}
      </div>

      {games.length === 0 ? (
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-12 text-center">
          <p className="text-2xl">🏀</p>
          <p className="mt-3 text-gray-400">No games scheduled today</p>
          {lastUpdated && (
            <p className="mt-1 text-sm text-gray-600">
              Last checked {lastUpdated.toLocaleTimeString()}
            </p>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {games.map((game) => (
            <GameCard key={game.game_id} game={game} />
          ))}
        </div>
      )}
    </section>
  );
}
