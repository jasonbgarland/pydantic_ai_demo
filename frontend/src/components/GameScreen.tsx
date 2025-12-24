/**
 * Game screen component with command input and narrative display
 */

"use client";

import { useState, useRef, useEffect } from "react";
import { GameSession } from "@/lib/api";

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
  onCommand: (command: string) => Promise<void>;
  onExit: () => void;
}

export function GameScreen({
  session,
  narrative,
  isLoading,
  onCommand,
  onExit,
}: GameScreenProps) {
  const [commandInput, setCommandInput] = useState("");
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
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
      {/* Character Stats Header */}
      <div className="border border-green-400 p-4 mb-4">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">
              {session.character.name.toUpperCase()}
            </h2>
            <p className="text-sm">
              Level {session.character.level}{" "}
              {session.character.character_class.charAt(0).toUpperCase() +
                session.character.character_class.slice(1)}
            </p>
          </div>

          <div className="grid grid-cols-5 gap-4 text-center">
            <div>
              <p className="font-bold text-xs">STR</p>
              <p className="text-lg">{session.character.stats.strength}</p>
            </div>
            <div>
              <p className="font-bold text-xs">MAG</p>
              <p className="text-lg">{session.character.stats.magic}</p>
            </div>
            <div>
              <p className="font-bold text-xs">AGI</p>
              <p className="text-lg">{session.character.stats.agility}</p>
            </div>
            <div>
              <p className="font-bold text-xs">HP</p>
              <p className="text-lg">{session.character.stats.health}</p>
            </div>
            <div>
              <p className="font-bold text-xs">STL</p>
              <p className="text-lg">{session.character.stats.stealth}</p>
            </div>
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
                className={`pl-4 ${
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
          {isLoading && (
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
      <div className="grid grid-cols-4 gap-2 mb-4">
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
          <p>• look / look around - Describe current location</p>
          <p>• go [direction] - Move (north, south, east, west)</p>
          <p>• examine [object] - Inspect something closely</p>
          <p>• take [item] - Pick up an item</p>
          <p>• use [item] - Use an item from inventory</p>
          <p>• inventory - Check your items</p>
          <p>• talk [entity] - Speak with someone</p>
          <p>• drop [item] - Drop an item</p>
        </div>
      </div>
    </div>
  );
}
