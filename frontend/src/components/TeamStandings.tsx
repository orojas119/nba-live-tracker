import type { Standing } from "../types";

interface Props {
  standings: { east: Standing[]; west: Standing[] };
}

function ConferenceTable({
  title,
  teams,
}: {
  title: string;
  teams: Standing[];
}) {
  return (
    <div className="mb-6">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-gray-500">
        {title}
      </h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-800 text-left text-xs uppercase tracking-wider text-gray-600">
            <th className="pb-2 pr-2 font-medium w-6">#</th>
            <th className="pb-2 font-medium">Team</th>
            <th className="pb-2 px-2 font-medium text-center">W</th>
            <th className="pb-2 px-2 font-medium text-center">L</th>
            <th className="pb-2 pl-2 font-medium text-right">PCT</th>
          </tr>
        </thead>
        <tbody>
          {teams.map((team, i) => (
            <tr
              key={team.team_name}
              className={`border-b border-gray-800/60 ${i % 2 === 0 ? "" : "bg-gray-800/20"}`}
            >
              <td className="py-2 pr-2 text-gray-600 text-xs">{team.rank}</td>
              <td className="py-2 font-medium text-gray-200 truncate max-w-0 w-full">
                {team.team_name}
              </td>
              <td className="py-2 px-2 text-center text-gray-300">
                {team.wins}
              </td>
              <td className="py-2 px-2 text-center text-gray-500">
                {team.losses}
              </td>
              <td className="py-2 pl-2 text-right font-mono text-xs text-gray-400">
                {team.win_pct.toFixed(3)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function TeamStandings({ standings }: Props) {
  return (
    <aside className="rounded-xl border border-gray-800 bg-gray-900 p-5 lg:sticky lg:top-6">
      <h2 className="mb-5 text-xs font-semibold uppercase tracking-widest text-gray-500">
        Standings
      </h2>
      <ConferenceTable title="Eastern Conference" teams={standings.east} />
      <ConferenceTable title="Western Conference" teams={standings.west} />
      <p className="mt-2 text-xs text-gray-700 text-center">Top 5 per conference</p>
    </aside>
  );
}
