import { useState } from "react";
import type { Game, PlayerStat } from "../types";
import { fetchBoxScore } from "../api/nba";

interface Props {
  game: Game;
}

function StatusBadge({ status }: { status: Game["game_status"] }) {
  if (status === "Live") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-red-500/30 bg-red-500/20 px-2.5 py-1 text-xs font-semibold uppercase tracking-wider text-red-400">
        <span className="h-1.5 w-1.5 rounded-full bg-red-400 animate-pulse" />
        Live
      </span>
    );
  }
  if (status === "Final") {
    return (
      <span className="inline-flex items-center rounded-full border border-gray-600 bg-gray-700/40 px-2.5 py-1 text-xs font-semibold uppercase tracking-wider text-gray-400">
        Final
      </span>
    );
  }
  return (
    <span className="inline-flex items-center rounded-full border border-blue-500/30 bg-blue-500/15 px-2.5 py-1 text-xs font-semibold uppercase tracking-wider text-blue-400">
      Scheduled
    </span>
  );
}

function BoxScoreModal({
  game,
  players,
  onClose,
}: {
  game: Game;
  players: PlayerStat[];
  onClose: () => void;
}) {
  const awayPlayers = players.slice(0, Math.ceil(players.length / 2));
  const homePlayersList = players.slice(Math.ceil(players.length / 2));

  const renderTable = (title: string, list: PlayerStat[]) => (
    <div className="mb-6">
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-gray-400">
        {title}
      </h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-700 text-left text-xs uppercase tracking-wider text-gray-500">
            <th className="pb-2 pr-4 font-medium">Player</th>
            <th className="pb-2 px-3 font-medium text-center">PTS</th>
            <th className="pb-2 px-3 font-medium text-center">REB</th>
            <th className="pb-2 px-3 font-medium text-center">AST</th>
            <th className="pb-2 pl-3 font-medium text-center">MIN</th>
          </tr>
        </thead>
        <tbody>
          {list.map((p, i) => (
            <tr
              key={i}
              className={`border-b border-gray-800 ${i % 2 === 0 ? "bg-gray-800/30" : ""}`}
            >
              <td className="py-2 pr-4 font-medium text-gray-200">
                {p.player_name}
              </td>
              <td className="py-2 px-3 text-center text-white font-semibold">
                {p.points}
              </td>
              <td className="py-2 px-3 text-center text-gray-300">{p.rebounds}</td>
              <td className="py-2 px-3 text-center text-gray-300">{p.assists}</td>
              <td className="py-2 pl-3 text-center text-gray-500">{p.minutes}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-lg max-h-[85vh] overflow-y-auto rounded-2xl border border-gray-700 bg-gray-900 p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-gray-500 hover:text-gray-300 transition-colors"
        >
          ✕
        </button>
        <h2 className="mb-5 text-lg font-bold text-white">
          {game.away_team} @ {game.home_team}
        </h2>
        {renderTable(game.away_team, awayPlayers)}
        {renderTable(game.home_team, homePlayersList)}
      </div>
    </div>
  );
}

export default function GameCard({ game }: Props) {
  const [showBoxScore, setShowBoxScore] = useState(false);
  const [players, setPlayers] = useState<PlayerStat[]>([]);
  const [loadingBox, setLoadingBox] = useState(false);

  const homeWinning =
    game.game_status !== "Scheduled" && game.home_score > game.away_score;
  const awayWinning =
    game.game_status !== "Scheduled" && game.away_score > game.home_score;

  const handleClick = async () => {
    if (game.game_status === "Scheduled") return;
    setLoadingBox(true);
    try {
      const data = await fetchBoxScore(game.game_id);
      setPlayers(data);
      setShowBoxScore(true);
    } catch {
      // silently ignore — no box score available
    } finally {
      setLoadingBox(false);
    }
  };

  return (
    <>
      <div
        onClick={handleClick}
        className={`rounded-xl border border-gray-800 bg-gray-900 p-6 transition-all duration-200
          ${game.game_status !== "Scheduled" ? "cursor-pointer hover:border-gray-600 hover:bg-gray-800/60" : ""}
          ${loadingBox ? "opacity-70" : ""}`}
      >
        {/* Status badge */}
        <div className="mb-4 flex items-center justify-between">
          <StatusBadge status={game.game_status} />
          {game.game_status === "Live" && game.period && (
            <span className="text-xs text-gray-500">
              Q{game.period}
              {game.game_clock ? ` · ${game.game_clock}` : ""}
            </span>
          )}
          {game.game_status !== "Live" && game.city && (
            <span className="text-xs text-gray-600">{game.city}</span>
          )}
        </div>

        {/* Scores */}
        <div className="space-y-3">
          {/* Away team */}
          <div className="flex items-center justify-between">
            <span
              className={`text-base font-semibold ${awayWinning ? "text-white" : "text-gray-400"}`}
            >
              {game.away_team}
            </span>
            <span
              className={`text-4xl font-bold tabular-nums ${awayWinning ? "text-white" : game.game_status === "Scheduled" ? "text-gray-600" : "text-gray-400"}`}
            >
              {game.game_status === "Scheduled" ? "–" : game.away_score}
            </span>
          </div>

          {/* Divider */}
          <div className="border-t border-gray-800" />

          {/* Home team */}
          <div className="flex items-center justify-between">
            <span
              className={`text-base font-semibold ${homeWinning ? "text-white" : "text-gray-400"}`}
            >
              {game.home_team}
            </span>
            <span
              className={`text-4xl font-bold tabular-nums ${homeWinning ? "text-white" : game.game_status === "Scheduled" ? "text-gray-600" : "text-gray-400"}`}
            >
              {game.game_status === "Scheduled" ? "–" : game.home_score}
            </span>
          </div>
        </div>

        {/* Footer hint */}
        {game.game_status !== "Scheduled" && (
          <p className="mt-4 text-center text-xs text-gray-600">
            {loadingBox ? "Loading box score..." : "Click to view box score"}
          </p>
        )}
      </div>

      {showBoxScore && players.length > 0 && (
        <BoxScoreModal
          game={game}
          players={players}
          onClose={() => setShowBoxScore(false)}
        />
      )}
    </>
  );
}
