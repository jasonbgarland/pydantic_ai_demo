/**
 * Unit tests for save/load API functions
 */
import { saveGame, loadGame, listSavedGames, deleteSavedGame } from "@/lib/api";

const API_BASE_URL = "http://localhost:8001";

describe("Save/Load API Functions", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  describe("saveGame", () => {
    it("should make POST request to save endpoint with correct data", async () => {
      const mockResponse = {
        game_id: "test-game-123",
        character_id: "char-456",
        session_name: "My Save",
        saved_at: "2025-12-28T10:00:00Z",
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await saveGame("test-game-123", "My Save");

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/game/test-game-123/save`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_name: "My Save" }),
        }
      );

      expect(result).toEqual(mockResponse);
    });

    it("should throw error when save fails", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        statusText: "Internal Server Error",
      });

      await expect(saveGame("test-game-123", "My Save")).rejects.toThrow(
        "Failed to save game: Internal Server Error"
      );
    });
  });

  describe("loadGame", () => {
    it("should make POST request to load endpoint", async () => {
      const mockResponse = {
        game_id: "test-game-123",
        session: {
          game_id: "test-game-123",
          character: { name: "Hero" },
          turn_count: 5,
        },
        message: "Loaded save: My Save",
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await loadGame("test-game-123");

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/game/test-game-123/load`,
        {
          method: "POST",
        }
      );

      expect(result).toEqual(mockResponse);
    });

    it("should throw error when load fails", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        statusText: "Not Found",
      });

      await expect(loadGame("test-game-123")).rejects.toThrow(
        "Failed to load game: Not Found"
      );
    });
  });

  describe("listSavedGames", () => {
    it("should make GET request to saves endpoint", async () => {
      const mockResponse = {
        saves: [
          {
            game_id: "game-1",
            session_name: "Save 1",
            character_name: "Hero",
            character_class: "warrior",
            level: 5,
            location: "Cave",
            turn_count: 10,
            last_played: "2025-12-28T10:00:00Z",
            created_at: "2025-12-27T08:00:00Z",
          },
        ],
        count: 1,
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await listSavedGames();

      expect(global.fetch).toHaveBeenCalledWith(`${API_BASE_URL}/game/saves`);
      expect(result).toEqual(mockResponse);
    });

    it("should throw error when list fails", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        statusText: "Service Unavailable",
      });

      await expect(listSavedGames()).rejects.toThrow(
        "Failed to list saved games: Service Unavailable"
      );
    });

    it("should handle empty saves list", async () => {
      const mockResponse = {
        saves: [],
        count: 0,
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await listSavedGames();

      expect(result.saves).toEqual([]);
      expect(result.count).toBe(0);
    });
  });

  describe("deleteSavedGame", () => {
    it("should make DELETE request to save endpoint", async () => {
      const mockResponse = {
        message: "Save deleted successfully",
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await deleteSavedGame("test-game-123");

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/game/test-game-123/save`,
        {
          method: "DELETE",
        }
      );

      expect(result).toEqual(mockResponse);
    });

    it("should throw error when delete fails", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        statusText: "Forbidden",
      });

      await expect(deleteSavedGame("test-game-123")).rejects.toThrow(
        "Failed to delete saved game: Forbidden"
      );
    });
  });

  describe("Network Errors", () => {
    it("should handle network errors in saveGame", async () => {
      (global.fetch as jest.Mock).mockRejectedValue(
        new Error("Network failure")
      );

      await expect(saveGame("test-game-123", "My Save")).rejects.toThrow(
        "Network failure"
      );
    });

    it("should handle network errors in loadGame", async () => {
      (global.fetch as jest.Mock).mockRejectedValue(
        new Error("Network failure")
      );

      await expect(loadGame("test-game-123")).rejects.toThrow(
        "Network failure"
      );
    });

    it("should handle network errors in listSavedGames", async () => {
      (global.fetch as jest.Mock).mockRejectedValue(
        new Error("Network failure")
      );

      await expect(listSavedGames()).rejects.toThrow("Network failure");
    });

    it("should handle network errors in deleteSavedGame", async () => {
      (global.fetch as jest.Mock).mockRejectedValue(
        new Error("Network failure")
      );

      await expect(deleteSavedGame("test-game-123")).rejects.toThrow(
        "Network failure"
      );
    });
  });
});
