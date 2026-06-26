import { useEffect, useState, useCallback } from "react";
import type { Game, Standing } from "./types";
import { fetchTodayGames, fetchStandings } from "./api/nba";
import ScoreBoard from "./components/ScoreBoard";
import TeamStandings from "./components/TeamStandings";

const EMPTY_STANDINGS = { east: [], west: [] };

export default function App() {
  const [games, setGames] = useState<Game[]>([]);
  const [standings, setStandings] = useState<{ east: Standing[]; west: Standing[] }>(EMPTY_STANDINGS);
  const [loadingGames, setLoadingGames] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const refreshGames = useCallback(async () => {
    try {
      const data = await fetchTodayGames();
      setGames(data);
      setLastUpdated(new Date());
    } catch (err) {
      console.error("Failed to fetch games:", err);
    } finally {
      setLoadingGames(false);
    }
  }, []);

  useEffect(() => {
    refreshGames();
    const interval = setInterval(refreshGames, 30_000);
    return () => clearInterval(interval);
  }, [refreshGames]);

  useEffect(() => {
    fetchStandings()
      .then(setStandings)
      .catch((err) => console.error("Failed to fetch standings:", err));
  }, []);

  const liveCount = games.filter((g) => g.game_status === "Live").length;

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-2xl">🏀</span>
              <div>
                <h1 className="text-xl font-bold tracking-tight text-white">
                  NBA Live Tracker
                </h1>
                <p className="text-xs text-gray-500">
                  2025–26 Season · Updates every 30 seconds
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {liveCount > 0 && (
                <span className="flex items-center gap-1.5 rounded-full border border-red-500/30 bg-red-500/15 px-3 py-1 text-xs font-semibold text-red-400">
                  <span className="h-1.5 w-1.5 rounded-full bg-red-400 animate-pulse" />
                  {liveCount} Live
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-8 lg:flex-row lg:gap-8">
          {/* Games grid — takes 2/3 of width on large screens */}
          <div className="flex-1 min-w-0">
            <ScoreBoard
              games={games}
              loading={loadingGames}
              lastUpdated={lastUpdated}
            />
          </div>

          {/* Standings sidebar — fixed width on large screens */}
          <div className="w-full lg:w-72 xl:w-80 shrink-0">
            {standings.east.length > 0 ? (
              <TeamStandings standings={standings} />
            ) : (
              <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
                <p className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-4">
                  Standings
                </p>
                <div className="flex items-center justify-center py-8">
                  <div className="h-8 w-8 rounded-full border-2 border-gray-700 border-t-orange-500 animate-spin" />
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-12 border-t border-gray-800 py-6">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <p className="text-center text-xs text-gray-700">
            Data from NBA API · Built with FastAPI + React
          </p>
        </div>
      </footer>
    </div>
  );
}
