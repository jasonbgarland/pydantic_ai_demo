/**
 * Custom hook for game state management and command processing
 */

import { useState, useCallback } from "react";
import {
  startGame,
  sendCommand,
  GameSession,
  CommandResponse,
} from "@/lib/api";

interface NarrativeEntry {
  turn: number;
  command?: string;
  response: string;
  agent?: string;
  success?: boolean;
}

export function useGame() {
  const [gameId, setGameId] = useState<string | null>(null);
  const [session, setSession] = useState<GameSession | null>(null);
  const [narrative, setNarrative] = useState<NarrativeEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Initialize a new game session
   */
  const initializeGame = useCallback(
    async (character: { name: string; character_class: string }) => {
      setIsLoading(true);
      setError(null);

      try {
        const { game_id, session: newSession } = await startGame(character);
        setGameId(game_id);
        setSession(newSession);

        // Add initial narrative
        setNarrative([
          {
            turn: 0,
            response: `Welcome, ${character.name}! You stand at the Cave Entrance, ready to begin your adventure.`,
          },
        ]);

        return game_id;
      } catch (err) {
        const errorMsg =
          err instanceof Error ? err.message : "Failed to start game";
        setError(errorMsg);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  /**
   * Execute a game command
   */
  const executeCommand = useCallback(
    async (command: string) => {
      if (!gameId) {
        setError("No active game session");
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const result: CommandResponse = await sendCommand(gameId, command);

        // Update session state
        setSession(result.session);

        // Add to narrative history
        setNarrative((prev) => [
          ...prev,
          {
            turn: result.turn,
            command,
            response: result.response,
            agent: result.agent,
            success: result.success,
          },
        ]);

        return result;
      } catch (err) {
        const errorMsg =
          err instanceof Error ? err.message : "Failed to execute command";
        setError(errorMsg);

        // Add error to narrative
        setNarrative((prev) => [
          ...prev,
          {
            turn: session?.turn_count || 0,
            command,
            response: `Error: ${errorMsg}`,
            success: false,
          },
        ]);

        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [gameId, session?.turn_count]
  );

  /**
   * Reset game state
   */
  const resetGame = useCallback(() => {
    setGameId(null);
    setSession(null);
    setNarrative([]);
    setError(null);
  }, []);

  // Track last active agent
  const lastAgent =
    narrative.length > 0 ? narrative[narrative.length - 1].agent || null : null;

  return {
    gameId,
    session,
    narrative,
    isLoading,
    error,
    lastAgent,
    initializeGame,
    executeCommand,
    resetGame,
  };
}
