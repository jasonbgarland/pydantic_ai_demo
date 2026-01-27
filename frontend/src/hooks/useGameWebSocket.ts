/**
 * Custom hook for WebSocket-based real-time game interaction
 * Provides streaming narrative responses and persistent connection management
 */

import { useState, useCallback, useEffect, useRef } from "react";
import { startGame, GameSession } from "@/lib/api";

interface NarrativeEntry {
  turn: number;
  command?: string;
  response: string;
  agent?: string;
  success?: boolean;
}

interface WebSocketMessage {
  type: "connected" | "typing" | "chunk" | "complete" | "error";
  game_id?: string;
  session?: GameSession;
  data?: string;
  agent?: string;
  turn?: number;
  success?: boolean;
  metadata?: any;
  message?: string;
  error?: string;
}

export function useGameWebSocket() {
  const [gameId, setGameId] = useState<string | null>(null);
  const [session, setSession] = useState<GameSession | null>(null);
  const [narrative, setNarrative] = useState<NarrativeEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const currentResponseRef = useRef<string>("");
  const currentTurnRef = useRef<number>(0);
  const currentCommandRef = useRef<string>("");
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Connect to WebSocket for given game_id
   */
  const connectWebSocket = useCallback(
    (id: string) => {
      // Close existing connection if any
      if (wsRef.current) {
        wsRef.current.close();
      }

      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsUrl = `${protocol}//localhost:8001/ws/game/${id}`;

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log("WebSocket connected");
        setIsConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        const message: WebSocketMessage = JSON.parse(event.data);

        switch (message.type) {
          case "connected":
            if (message.session) {
              setSession(message.session);
            }
            break;

          case "typing":
            setIsTyping(true);
            currentResponseRef.current = "";
            // Set the turn ref here when typing starts, not when sending command
            currentTurnRef.current = (session?.turn_count || 0) + 1;
            break;

          case "chunk":
            // Accumulate streaming text chunks
            if (message.data) {
              currentResponseRef.current += message.data;

              // Update the last narrative entry with accumulated text
              setNarrative((prev) => {
                const updated = [...prev];
                const lastEntry =
                  updated.length > 0 ? updated[updated.length - 1] : null;

                if (
                  lastEntry &&
                  lastEntry.turn === currentTurnRef.current &&
                  lastEntry.command === currentCommandRef.current
                ) {
                  // Update existing entry
                  updated[updated.length - 1] = {
                    ...updated[updated.length - 1],
                    response: currentResponseRef.current,
                  };
                } else {
                  // Create new entry
                  updated.push({
                    turn: currentTurnRef.current,
                    command: currentCommandRef.current,
                    response: currentResponseRef.current,
                  });
                }
                return updated;
              });
            }
            break;

          case "complete":
            setIsTyping(false);
            setIsLoading(false);

            // Update session with final state
            if (message.session) {
              setSession(message.session);
            }

            // Finalize narrative entry with complete data
            const finalResponse = currentResponseRef.current; // Capture before any resets
            setNarrative((prev) => {
              const updated = [...prev];
              if (
                updated.length > 0 &&
                updated[updated.length - 1].turn === currentTurnRef.current
              ) {
                updated[updated.length - 1] = {
                  ...updated[updated.length - 1],
                  response: finalResponse, // Ensure final response is preserved
                  agent: message.agent,
                  success: message.success,
                };
              }
              return updated;
            });
            // Note: currentResponseRef will be reset when next "typing" message arrives
            break;

          case "error":
            setIsTyping(false);
            setIsLoading(false);
            setError(message.message || message.error || "Unknown error");

            // Add error to narrative
            setNarrative((prev) => [
              ...prev,
              {
                turn: currentTurnRef.current,
                command: currentCommandRef.current,
                response: message.message || "An error occurred",
                success: false,
              },
            ]);
            break;
        }
      };

      ws.onerror = (err) => {
        console.error("WebSocket error:", err);
        setError("Connection error occurred");
      };

      ws.onclose = () => {
        console.log("WebSocket disconnected");
        setIsConnected(false);

        // Attempt reconnection after delay (if game is still active)
        if (gameId) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log("Attempting to reconnect...");
            connectWebSocket(id);
          }, 3000);
        }
      };

      wsRef.current = ws;
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [gameId],
  );

  /**
   * Initialize a new game session
   */
  const initializeGame = useCallback(
    async (character: { name: string }) => {
      setIsLoading(true);
      setError(null);

      try {
        // Create session via REST API
        const response = await startGame(character);
        const { game_id, session: newSession, intro_narrative } = response;
        setGameId(game_id);
        setSession(newSession);

        // Add introduction narrative if provided, otherwise use default
        const welcomeMessage =
          intro_narrative ||
          `Welcome, ${character.name}! You stand at the Cave Entrance, ready to begin your adventure.`;

        setNarrative([
          {
            turn: 0,
            response: welcomeMessage,
          },
        ]);

        // Connect WebSocket for real-time updates
        connectWebSocket(game_id);

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
    // connectWebSocket is defined outside with its own dependencies
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  /**
   * Execute a game command via WebSocket
   */
  const executeCommand = useCallback(
    (command: string) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        setError("Not connected to game server");
        return;
      }

      setIsLoading(true);
      setError(null);

      // Store command for narrative
      currentCommandRef.current = command;
      currentTurnRef.current = (session?.turn_count || 0) + 1;

      // Send command via WebSocket
      wsRef.current.send(
        JSON.stringify({
          command,
          parameters: null,
        }),
      );
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [session],
  );

  /**
   * Load an existing game session
   */
  const loadGameSession = useCallback(
    (id: string, loadedSession: GameSession) => {
      setGameId(id);
      setSession(loadedSession);

      // Create initial narrative from loaded state
      setNarrative([
        {
          turn: 0,
          response: `Game loaded. You are at ${loadedSession.location}. Turn ${loadedSession.turn_count}.`,
        },
      ]);

      // Connect WebSocket for real-time updates
      connectWebSocket(id);
    },
    [connectWebSocket],
  );

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return {
    gameId,
    session,
    narrative,
    isLoading,
    isTyping,
    isConnected,
    error,
    initializeGame,
    loadGameSession,
    executeCommand,
  };
}
