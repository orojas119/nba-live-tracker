export interface Game {
  game_id: string;
  home_team: string;
  away_team: string;
  home_score: number;
  away_score: number;
  game_status: "Live" | "Final" | "Scheduled";
  game_clock?: string;
  period?: number;
  arena?: string;
  city?: string;
}

export interface Standing {
  team_name: string;
  wins: number;
  losses: number;
  win_pct: number;
  conference: string;
  rank: number;
}

export interface PlayerStat {
  player_name: string;
  team: string;
  points: number;
  rebounds: number;
  assists: number;
  minutes: string;
}
