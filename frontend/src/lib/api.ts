/**
 * API client for Adventure Engine backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export interface Character {
  name: string;
  character_class: string;
  stats: {
    strength: number;
    magic: number;
    agility: number;
    health: number;
    stealth: number;
  };
  level: number;
}

export interface GameSession {
  game_id: string;
  character: Character;
  location: string;
  inventory: string[];
  visited_rooms: string[];
  turn_count: number;
  created_at: string;
  updated_at: string;
  history?: Array<{
    turn: number;
    command: string;
    response?: string;
  }>;
}

export interface CommandResponse {
  game_id: string;
  turn: number;
  response: string;
  agent: string;
  success: boolean;
  session: GameSession;
  metadata?: Record<string, any>;
  error?: string;
}

/**
 * Start a new game session
 */
export async function startGame(character: {
  name: string;
  character_class: string;
}): Promise<{ game_id: string; session: GameSession }> {
  const response = await fetch(`${API_BASE_URL}/game/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(character),
  });

  if (!response.ok) {
    throw new Error(`Failed to start game: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Send a command to the game
 */
export async function sendCommand(
  gameId: string,
  command: string,
  parameters?: Record<string, any>
): Promise<CommandResponse> {
  const response = await fetch(`${API_BASE_URL}/game/${gameId}/command`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ command, parameters }),
  });

  if (!response.ok) {
    throw new Error(`Failed to send command: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get current game state
 */
export async function getGameState(gameId: string): Promise<GameSession> {
  const response = await fetch(`${API_BASE_URL}/game/${gameId}/state`);

  if (!response.ok) {
    throw new Error(`Failed to get game state: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Save game to database
 */
export async function saveGame(
  gameId: string,
  sessionName: string
): Promise<{
  game_id: string;
  character_id: number;
  session_name: string;
  saved_at: string;
}> {
  const response = await fetch(`${API_BASE_URL}/game/${gameId}/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_name: sessionName }),
  });

  if (!response.ok) {
    throw new Error(`Failed to save game: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Load game from database
 */
export async function loadGame(gameId: string): Promise<{
  game_id: string;
  session: GameSession;
  message: string;
}> {
  const response = await fetch(`${API_BASE_URL}/game/${gameId}/load`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(`Failed to load game: ${response.statusText}`);
  }

  return response.json();
}

/**
 * List all saved games
 */
export async function listSavedGames(): Promise<{
  saves: Array<{
    game_id: string;
    session_name: string;
    character_name: string;
    character_class: string;
    level: number;
    location: string;
    turn_count: number;
    last_played: string;
    created_at: string;
  }>;
  count: number;
}> {
  const response = await fetch(`${API_BASE_URL}/game/saves`);

  if (!response.ok) {
    throw new Error(`Failed to list saved games: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Delete a saved game
 */
export async function deleteSavedGame(gameId: string): Promise<{
  message: string;
}> {
  const response = await fetch(`${API_BASE_URL}/game/${gameId}/save`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error(`Failed to delete saved game: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Health check for backend
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.ok;
  } catch {
    return false;
  }
}
