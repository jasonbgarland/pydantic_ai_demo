/**
 * Modal for loading saved games from database
 */

"use client";

import { useState, useEffect } from "react";

interface SavedGame {
  game_id: string;
  session_name: string;
  character_name: string;
  character_class: string;
  level: number;
  location: string;
  turn_count: number;
  last_played: string;
  created_at: string;
}

interface LoadGameModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLoad: (gameId: string) => Promise<void>;
  onDelete: (gameId: string) => Promise<void>;
  onFetchSaves: () => Promise<SavedGame[]>;
}

export function LoadGameModal({
  isOpen,
  onClose,
  onLoad,
  onDelete,
  onFetchSaves,
}: LoadGameModalProps) {
  const [savedGames, setSavedGames] = useState<SavedGame[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingGame, setIsLoadingGame] = useState<string | null>(null);
  const [isDeletingGame, setIsDeletingGame] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchSavedGames();
    }
  }, [isOpen]);

  const fetchSavedGames = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const games = await onFetchSaves();
      setSavedGames(games);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load saved games"
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoad = async (gameId: string) => {
    setIsLoadingGame(gameId);
    setError(null);
    try {
      await onLoad(gameId);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load game");
    } finally {
      setIsLoadingGame(null);
    }
  };

  const handleDelete = async (gameId: string) => {
    if (!confirm("Are you sure you want to delete this save?")) {
      return;
    }

    setIsDeletingGame(gameId);
    setError(null);
    try {
      await onDelete(gameId);
      setSavedGames((prev) => prev.filter((game) => game.game_id !== gameId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete game");
    } finally {
      setIsDeletingGame(null);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + " " + date.toLocaleTimeString();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-gray-900 border-2 border-green-500 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        <h2 className="text-2xl font-bold text-green-400 mb-4">Load Game</h2>

        {error && (
          <div className="mb-4 p-3 bg-red-900 border border-red-500 rounded">
            <p className="text-red-300">{error}</p>
          </div>
        )}

        {isLoading ? (
          <div className="text-center py-8">
            <p className="text-green-300">Loading saved games...</p>
          </div>
        ) : savedGames.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-green-300">No saved games found.</p>
          </div>
        ) : (
          <div className="space-y-3 mb-4">
            {savedGames.map((game) => (
              <div
                key={game.game_id}
                className="bg-gray-800 border border-green-500 rounded p-4 hover:border-green-400 transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-green-400 mb-1">
                      {game.session_name}
                    </h3>
                    <p className="text-green-300 text-sm mb-2">
                      {game.character_name} - Level {game.level}{" "}
                      {game.character_class}
                    </p>
                    <div className="text-green-300 text-sm space-y-1">
                      <p>
                        <span className="text-gray-400">Location:</span>{" "}
                        {game.location}
                      </p>
                      <p>
                        <span className="text-gray-400">Turn:</span>{" "}
                        {game.turn_count}
                      </p>
                      <p>
                        <span className="text-gray-400">Last Played:</span>{" "}
                        {formatDate(game.last_played)}
                      </p>
                    </div>
                  </div>

                  <div className="flex flex-col gap-2">
                    <button
                      onClick={() => handleLoad(game.game_id)}
                      disabled={
                        isLoadingGame === game.game_id ||
                        isDeletingGame === game.game_id
                      }
                      className="bg-green-600 hover:bg-green-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-bold py-2 px-4 rounded transition-colors whitespace-nowrap"
                    >
                      {isLoadingGame === game.game_id ? "Loading..." : "Load"}
                    </button>
                    <button
                      onClick={() => handleDelete(game.game_id)}
                      disabled={
                        isLoadingGame === game.game_id ||
                        isDeletingGame === game.game_id
                      }
                      className="bg-red-600 hover:bg-red-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-bold py-2 px-4 rounded transition-colors whitespace-nowrap"
                    >
                      {isDeletingGame === game.game_id
                        ? "Deleting..."
                        : "Delete"}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="flex justify-end">
          <button
            onClick={onClose}
            disabled={isLoadingGame !== null || isDeletingGame !== null}
            className="bg-gray-700 hover:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-2 px-6 rounded transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
