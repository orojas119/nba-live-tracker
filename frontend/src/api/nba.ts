import axios from "axios";
import type { Game, Standing, PlayerStat } from "../types";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const fetchTodayGames = async (): Promise<Game[]> => {
  const res = await axios.get(`${BASE_URL}/api/games/today`);
  return res.data.games;
};

export const fetchStandings = async (): Promise<{
  east: Standing[];
  west: Standing[];
}> => {
  const res = await axios.get(`${BASE_URL}/api/standings`);
  return res.data;
};

export const fetchBoxScore = async (gameId: string): Promise<PlayerStat[]> => {
  const res = await axios.get(`${BASE_URL}/api/games/${gameId}/boxscore`);
  return res.data.players;
};
