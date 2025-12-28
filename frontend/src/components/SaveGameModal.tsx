/**
 * Modal for saving current game to database
 */

"use client";

import { useState } from "react";

interface SaveGameModalProps {
  gameId: string;
  isOpen: boolean;
  onClose: () => void;
  onSave: (sessionName: string) => Promise<void>;
}

export function SaveGameModal({
  gameId,
  isOpen,
  onClose,
  onSave,
}: SaveGameModalProps) {
  const [sessionName, setSessionName] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  if (!isOpen) return null;

  const handleSave = async () => {
    if (!sessionName.trim()) {
      setError("Please enter a save name");
      return;
    }

    setIsSaving(true);
    setError(null);

    try {
      await onSave(sessionName.trim());
      setSuccess(true);
      setTimeout(() => {
        onClose();
        setSuccess(false);
        setSessionName("");
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save game");
    } finally {
      setIsSaving(false);
    }
  };

  const handleClose = () => {
    if (!isSaving) {
      onClose();
      setSessionName("");
      setError(null);
      setSuccess(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-gray-900 border-2 border-green-500 rounded-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-2xl font-bold text-green-400 mb-4">Save Game</h2>

        {success ? (
          <div className="text-center py-4">
            <p className="text-green-400 text-lg">✓ Game saved successfully!</p>
          </div>
        ) : (
          <>
            <div className="mb-4">
              <label
                htmlFor="sessionName"
                className="block text-green-300 mb-2"
              >
                Save Name:
              </label>
              <input
                id="sessionName"
                type="text"
                value={sessionName}
                onChange={(e) => setSessionName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !isSaving) {
                    handleSave();
                  } else if (e.key === "Escape") {
                    handleClose();
                  }
                }}
                placeholder="My Adventure"
                disabled={isSaving}
                className="w-full bg-gray-800 border border-green-500 text-green-300 px-3 py-2 rounded focus:outline-none focus:border-green-400 disabled:opacity-50"
                autoFocus
              />
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-900 border border-red-500 rounded">
                <p className="text-red-300">{error}</p>
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={handleSave}
                disabled={isSaving || !sessionName.trim()}
                className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-bold py-2 px-4 rounded transition-colors"
              >
                {isSaving ? "Saving..." : "Save"}
              </button>
              <button
                onClick={handleClose}
                disabled={isSaving}
                className="flex-1 bg-gray-700 hover:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-2 px-4 rounded transition-colors"
              >
                Cancel
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
