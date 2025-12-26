/**
 * Tests for useGameWebSocket hook
 */
import { renderHook, act, waitFor } from "@testing-library/react";
import { useGameWebSocket } from "@/hooks/useGameWebSocket";
import WS from "jest-websocket-mock";

// Mock the API module
jest.mock("@/lib/api", () => ({
  startGame: jest.fn(),
}));

describe("useGameWebSocket", () => {
  let server: WS;

  beforeEach(() => {
    // Create mock WebSocket server
    server = new WS("ws://localhost:8001/ws/game/test-game-id");
  });

  afterEach(() => {
    WS.clean();
  });

  describe("Connection Management", () => {
    it("should initialize with disconnected state", () => {
      const { result } = renderHook(() => useGameWebSocket());

      expect(result.current.isConnected).toBe(false);
      expect(result.current.gameId).toBeNull();
      expect(result.current.session).toBeNull();
      expect(result.current.narrative).toEqual([]);
    });

    it("should establish WebSocket connection when game initializes", async () => {
      const { startGame } = require("@/lib/api");
      startGame.mockResolvedValue({
        game_id: "test-game-id",
        session: { turn_count: 0, character: { name: "Test" } },
      });

      const { result } = renderHook(() => useGameWebSocket());

      await act(async () => {
        await result.current.initializeGame({
          name: "TestChar",
          character_class: "Warrior",
        });
      });

      await server.connected;

      // Send connected message
      await act(async () => {
        server.send(
          JSON.stringify({
            type: "connected",
            game_id: "test-game-id",
            session: { turn_count: 0 },
          })
        );
      });

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
        expect(result.current.gameId).toBe("test-game-id");
      });
    });
  });

  describe("Message Handling", () => {
    it("should handle connected message and update session", async () => {
      const { startGame } = require("@/lib/api");
      startGame.mockResolvedValue({
        game_id: "test-game-id",
        session: { turn_count: 0 },
      });

      const { result } = renderHook(() => useGameWebSocket());

      await act(async () => {
        await result.current.initializeGame({
          name: "Test",
          character_class: "Warrior",
        });
      });

      await server.connected;

      await act(async () => {
        server.send(
          JSON.stringify({
            type: "connected",
            game_id: "test-game-id",
            session: {
              turn_count: 0,
              character: { name: "Test", class: "Warrior" },
            },
          })
        );
      });

      await waitFor(() => {
        expect(result.current.session).toBeTruthy();
        expect(result.current.session?.character.name).toBe("Test");
      });
    });

    it("should handle typing indicator", async () => {
      const { startGame } = require("@/lib/api");
      startGame.mockResolvedValue({
        game_id: "test-game-id",
        session: { turn_count: 0 },
      });

      const { result } = renderHook(() => useGameWebSocket());

      await act(async () => {
        await result.current.initializeGame({
          name: "Test",
          character_class: "Warrior",
        });
      });

      await server.connected;

      await act(async () => {
        server.send(
          JSON.stringify({ type: "connected", game_id: "test-game-id" })
        );
        server.send(
          JSON.stringify({ type: "typing", agent: "RoomDescriptor" })
        );
      });

      await waitFor(() => {
        expect(result.current.isTyping).toBe(true);
      });
    });

    it("should accumulate chunks into narrative response", async () => {
      const { startGame } = require("@/lib/api");
      startGame.mockResolvedValue({
        game_id: "test-game-id",
        session: { turn_count: 0 },
      });

      const { result } = renderHook(() => useGameWebSocket());

      await act(async () => {
        await result.current.initializeGame({
          name: "Test",
          character_class: "Warrior",
        });
      });

      await server.connected;

      await act(async () => {
        server.send(
          JSON.stringify({ type: "connected", game_id: "test-game-id" })
        );
      });

      // Execute command
      await act(async () => {
        result.current.executeCommand("look around");
      });

      // Receive typing then chunks
      await act(async () => {
        server.send(
          JSON.stringify({ type: "typing", agent: "RoomDescriptor" })
        );
        server.send(JSON.stringify({ type: "chunk", data: "You" }));
        server.send(JSON.stringify({ type: "chunk", data: " stand" }));
        server.send(JSON.stringify({ type: "chunk", data: " at" }));
        server.send(JSON.stringify({ type: "chunk", data: " the" }));
        server.send(JSON.stringify({ type: "chunk", data: " entrance." }));
      });

      await waitFor(() => {
        const lastEntry =
          result.current.narrative[result.current.narrative.length - 1];
        expect(lastEntry?.response).toBe("You stand at the entrance.");
      });
    });

    it("should finalize narrative on complete message", async () => {
      const { startGame } = require("@/lib/api");
      startGame.mockResolvedValue({
        game_id: "test-game-id",
        session: { turn_count: 0 },
      });

      const { result } = renderHook(() => useGameWebSocket());

      await act(async () => {
        await result.current.initializeGame({
          name: "Test",
          character_class: "Warrior",
        });
      });

      await server.connected;

      await act(async () => {
        server.send(
          JSON.stringify({ type: "connected", game_id: "test-game-id" })
        );
      });

      await act(async () => {
        result.current.executeCommand("look");
      });

      await act(async () => {
        server.send(
          JSON.stringify({ type: "typing", agent: "RoomDescriptor" })
        );
        server.send(JSON.stringify({ type: "chunk", data: "Test response" }));
        server.send(
          JSON.stringify({
            type: "complete",
            game_id: "test-game-id",
            turn: 1,
            agent: "RoomDescriptor",
            success: true,
            session: { turn_count: 1 },
          })
        );
      });

      await waitFor(() => {
        expect(result.current.isTyping).toBe(false);
        expect(result.current.isLoading).toBe(false);
        const lastEntry =
          result.current.narrative[result.current.narrative.length - 1];
        expect(lastEntry?.agent).toBe("RoomDescriptor");
        expect(lastEntry?.success).toBe(true);
      });
    });

    it("should handle error messages", async () => {
      const { startGame } = require("@/lib/api");
      startGame.mockResolvedValue({
        game_id: "test-game-id",
        session: { turn_count: 0 },
      });

      const { result } = renderHook(() => useGameWebSocket());

      await act(async () => {
        await result.current.initializeGame({
          name: "Test",
          character_class: "Warrior",
        });
      });

      await server.connected;

      await act(async () => {
        server.send(
          JSON.stringify({ type: "connected", game_id: "test-game-id" })
        );
        server.send(
          JSON.stringify({
            type: "error",
            message: "Command failed",
          })
        );
      });

      await waitFor(() => {
        expect(result.current.error).toBe("Command failed");
        expect(result.current.isTyping).toBe(false);
        expect(result.current.isLoading).toBe(false);
      });
    });
  });

  describe("Command Execution", () => {
    it("should send command via WebSocket when connected", async () => {
      const { startGame } = require("@/lib/api");
      startGame.mockResolvedValue({
        game_id: "test-game-id",
        session: { turn_count: 0 },
      });

      const { result } = renderHook(() => useGameWebSocket());

      await act(async () => {
        await result.current.initializeGame({
          name: "Test",
          character_class: "Warrior",
        });
      });

      await server.connected;

      await act(async () => {
        server.send(
          JSON.stringify({ type: "connected", game_id: "test-game-id" })
        );
      });

      await act(async () => {
        result.current.executeCommand("look around");
      });

      const message = await server.nextMessage;
      const parsed = JSON.parse(message as string);

      expect(parsed.command).toBe("look around");
      expect(parsed.parameters).toBeNull();
    });

    it("should not send command when WebSocket is not connected", async () => {
      const { result } = renderHook(() => useGameWebSocket());

      act(() => {
        result.current.executeCommand("look around");
      });

      expect(result.current.error).toBe("Not connected to game server");
    });
  });

  describe("State Management", () => {
    it("should update narrative array with new entries", async () => {
      const { startGame } = require("@/lib/api");
      startGame.mockResolvedValue({
        game_id: "test-game-id",
        session: { turn_count: 0 },
      });

      const { result } = renderHook(() => useGameWebSocket());

      await act(async () => {
        await result.current.initializeGame({
          name: "Test",
          character_class: "Warrior",
        });
      });

      // Should have initial welcome message
      expect(result.current.narrative.length).toBeGreaterThan(0);
      expect(result.current.narrative[0].response).toContain("Welcome");
    });

    it("should preserve response text in complete message", async () => {
      const { startGame } = require("@/lib/api");
      startGame.mockResolvedValue({
        game_id: "test-game-id",
        session: { turn_count: 0 },
      });

      const { result } = renderHook(() => useGameWebSocket());

      await act(async () => {
        await result.current.initializeGame({
          name: "Test",
          character_class: "Warrior",
        });
      });

      await server.connected;

      await act(async () => {
        server.send(
          JSON.stringify({
            type: "connected",
            game_id: "test-game-id",
            session: { turn_count: 0 },
          })
        );
      });

      await act(async () => {
        result.current.executeCommand("test command");
      });

      await act(async () => {
        server.send(JSON.stringify({ type: "typing", agent: "Test" }));
        server.send(JSON.stringify({ type: "chunk", data: "Full" }));
        server.send(JSON.stringify({ type: "chunk", data: " response" }));
        server.send(
          JSON.stringify({
            type: "complete",
            game_id: "test-game-id",
            turn: 1,
            agent: "Test",
            success: true,
            session: { turn_count: 1 },
          })
        );
      });

      await waitFor(() => {
        const lastEntry =
          result.current.narrative[result.current.narrative.length - 1];
        expect(lastEntry?.response).toBe("Full response");
      });
    });
  });
});
