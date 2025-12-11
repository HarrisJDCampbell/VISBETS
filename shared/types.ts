export interface Player {
  id: string;
  name: string;
  team: string;
  position: string;
  stats: PlayerStats;
}

export interface PlayerStats {
  gamesPlayed: number;
  points: number;
  assists: number;
  rebounds: number;
}

export interface User {
  id: string;
  username: string;
  email: string;
  favorites: string[]; // Array of player IDs
} 