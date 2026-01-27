/**
 * Game screen component with command input and narrative display
 */

"use client";

import { useState, useRef, useEffect } from "react";
import { GameSession } from "@/lib/api";
import { SaveGameModal } from "./SaveGameModal";
import { LoadGameModal } from "./LoadGameModal";

interface NarrativeEntry {
  turn: number;
  command?: string;
  response: string;
  agent?: string;
  success?: boolean;
}

interface GameScreenProps {
  session: GameSession;
  narrative: NarrativeEntry[];
  isLoading: boolean;
  isTyping?: boolean; // New: WebSocket typing indicator
  isConnected?: boolean; // New: WebSocket connection status
  onCommand: (command: string) => Promise<void> | void; // Updated: can be sync for WebSocket
  onExit: () => void;
  onSave?: (sessionName: string) => Promise<void>;
  onLoad?: (gameId: string) => Promise<void>;
  onDelete?: (gameId: string) => Promise<void>;
  onFetchSaves?: () => Promise<any[]>;
}

export function GameScreen({
  session,
  narrative,
  isLoading,
  isTyping = false,
  isConnected = true,
  onCommand,
  onExit,
  onSave,
  onLoad,
  onDelete,
  onFetchSaves,
}: GameScreenProps) {
  const [commandInput, setCommandInput] = useState("");
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [showLoadModal, setShowLoadModal] = useState(false);
  const narrativeEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when narrative updates
  useEffect(() => {
    narrativeEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [narrative]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmitCommand = async (e: React.FormEvent) => {
    e.preventDefault();

    const command = commandInput.trim();
    if (!command || isLoading) return;

    // Add to command history
    setCommandHistory((prev) => [...prev, command]);
    setHistoryIndex(-1);
    setCommandInput("");

    try {
      await onCommand(command);
    } catch (err) {
      console.error("Command failed:", err);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    // Navigate command history with arrow keys
    if (e.key === "ArrowUp") {
      e.preventDefault();
      if (commandHistory.length === 0) return;

      const newIndex =
        historyIndex === -1
          ? commandHistory.length - 1
          : Math.max(0, historyIndex - 1);

      setHistoryIndex(newIndex);
      setCommandInput(commandHistory[newIndex]);
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      if (historyIndex === -1) return;

      const newIndex = historyIndex + 1;

      if (newIndex >= commandHistory.length) {
        setHistoryIndex(-1);
        setCommandInput("");
      } else {
        setHistoryIndex(newIndex);
        setCommandInput(commandHistory[newIndex]);
      }
    }
  };

  return (
    <div className="max-w-5xl w-full">
      {/* Character Header */}
      <div className="border border-green-400 p-4 mb-4">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">
              {session.character.name.toUpperCase()}
            </h2>
            <p className="text-sm">
              Level {session.character.level} Adventurer
            </p>
          </div>

          <div className="text-right text-sm">
            <p>
              Location:{" "}
              <span className="text-yellow-400">{session.location}</span>
            </p>
            <p>
              Turn: <span className="text-blue-400">{session.turn_count}</span>
            </p>
            {session.inventory.length > 0 && (
              <p>
                Items:{" "}
                <span className="text-purple-400">
                  {session.inventory.length}
                </span>
              </p>
            )}
            <p className="mt-1">
              {isConnected ? (
                <span className="text-green-400 text-xs">● Connected</span>
              ) : (
                <span className="text-red-400 text-xs">● Disconnected</span>
              )}
            </p>
          </div>
        </div>
      </div>

      {/* Narrative Display */}
      <div className="border border-green-400 p-4 mb-4 h-96 overflow-y-auto bg-black">
        <div className="space-y-4">
          {narrative.map((entry, index) => (
            <div key={index} className="narrative-entry">
              {entry.command && (
                <p className="text-yellow-400 mb-1">&gt; {entry.command}</p>
              )}
              <p
                className={`pl-4 whitespace-pre-line ${
                  entry.success === false ? "text-red-400" : "text-green-400"
                }`}
              >
                {entry.response}
              </p>
              {entry.agent && (
                <p className="text-xs text-gray-500 pl-4 mt-1">
                  [Processed by: {entry.agent}]
                </p>
              )}
            </div>
          ))}
          {isTyping && (
            <p className="text-blue-400 animate-pulse">
              &gt; Agent is thinking<span className="animate-pulse">...</span>
            </p>
          )}
          {isLoading && !isTyping && (
            <p className="text-blue-400 animate-pulse">
              &gt; Processing command...
            </p>
          )}
          <div ref={narrativeEndRef} />
        </div>
      </div>

      {/* Command Input */}
      <form onSubmit={handleSubmitCommand} className="mb-4">
        <div className="flex gap-2">
          <span className="text-green-400 self-center">&gt;</span>
          <input
            ref={inputRef}
            type="text"
            value={commandInput}
            onChange={(e) => setCommandInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter command (look, go north, examine, inventory, etc.)..."
            className="flex-1 bg-black border border-green-400 text-green-400 p-2 focus:outline-none focus:border-yellow-400"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!commandInput.trim() || isLoading}
            className="bg-green-400 text-black px-6 py-2 disabled:bg-gray-600 disabled:text-gray-400 hover:bg-yellow-400 transition-colors"
          >
            {isLoading ? "Processing..." : "Execute"}
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          Tip: Use ↑↓ arrow keys to navigate command history
        </p>
      </form>

      {/* Quick Commands */}
      <div className="grid grid-cols-6 gap-2 mb-4">
        <button
          onClick={() => onCommand("look around")}
          disabled={isLoading}
          className="border border-green-400 p-2 hover:bg-green-400 hover:text-black disabled:opacity-50 text-sm"
        >
          Look Around
        </button>
        <button
          onClick={() => onCommand("inventory")}
          disabled={isLoading}
          className="border border-green-400 p-2 hover:bg-green-400 hover:text-black disabled:opacity-50 text-sm"
        >
          Inventory
        </button>
        <button
          onClick={() => onCommand("examine room")}
          disabled={isLoading}
          className="border border-green-400 p-2 hover:bg-green-400 hover:text-black disabled:opacity-50 text-sm"
        >
          Examine
        </button>
        {onSave && (
          <button
            onClick={() => setShowSaveModal(true)}
            disabled={isLoading}
            className="border border-blue-400 text-blue-400 p-2 hover:bg-blue-400 hover:text-black disabled:opacity-50 text-sm"
          >
            Save Game
          </button>
        )}
        {onLoad && onFetchSaves && (
          <button
            onClick={() => setShowLoadModal(true)}
            disabled={isLoading}
            className="border border-purple-400 text-purple-400 p-2 hover:bg-purple-400 hover:text-black disabled:opacity-50 text-sm"
          >
            Load Game
          </button>
        )}
        <button
          onClick={onExit}
          className="border border-red-400 text-red-400 p-2 hover:bg-red-400 hover:text-black text-sm"
        >
          Exit Game
        </button>
      </div>

      {/* Help Text */}
      <div className="border border-gray-600 p-3 text-xs text-gray-500">
        <p className="font-bold mb-1">Common Commands:</p>
        <div className="grid grid-cols-2 gap-1">
          <p>• look around - Describe current location</p>
          <p>• go [direction] - Move between rooms</p>
          <p>• examine [item] - Inspect items closely</p>
          <p>• take [item] - Pick up items</p>
          <p>• claim crystal - Retrieve the prize</p>
          <p>• cross chasm - Cross obstacles</p>
          <p>• escape - Leave the cave</p>
          <p>• inventory - Check your items</p>
        </div>
      </div>

      {/* Save/Load Modals */}
      {onSave && (
        <SaveGameModal
          gameId={session.game_id}
          isOpen={showSaveModal}
          onClose={() => setShowSaveModal(false)}
          onSave={onSave}
        />
      )}
      {onLoad && onDelete && onFetchSaves && (
        <LoadGameModal
          isOpen={showLoadModal}
          onClose={() => setShowLoadModal(false)}
          onLoad={onLoad}
          onDelete={onDelete}
          onFetchSaves={onFetchSaves}
        />
      )}
    </div>
  );
}
