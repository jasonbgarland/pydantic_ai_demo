"use client";

import { useState, useEffect } from "react";
import { useGameWebSocket } from "@/hooks/useGameWebSocket";
import { GameScreen } from "@/components/GameScreen";
import { LoadGameModal } from "@/components/LoadGameModal";
import { saveGame, loadGame, listSavedGames, deleteSavedGame } from "@/lib/api";

interface Character {
  name: string;
  character_class: string;
  level: number;
}

type GameState = "main" | "character-creation" | "game";

export default function Home() {
  const [gameState, setGameState] = useState<GameState>("main");
  const [backendStatus, setBackendStatus] = useState<
    "checking" | "connected" | "failed"
  >("checking");
  const [characterName, setCharacterName] = useState<string>("");
  const [character, setCharacter] = useState<Character | null>(null);
  const [showLoadModal, setShowLoadModal] = useState(false);

  // Game state management hook with WebSocket
  const {
    session,
    narrative,
    isLoading,
    isTyping,
    isConnected,
    error: gameError,
    initializeGame,
    loadGameSession,
    executeCommand,
  } = useGameWebSocket();

  useEffect(() => {
    const checkBackendHealth = async () => {
      try {
        const response = await fetch("http://localhost:8001/health");
        if (response.ok) {
          setBackendStatus("connected");
        } else {
          setBackendStatus("failed");
        }
      } catch (error) {
        console.error("Backend health check failed:", error);
        setBackendStatus("failed");
      }
    };

    checkBackendHealth();
  }, []);

  const getStatusDisplay = () => {
    switch (backendStatus) {
      case "checking":
        return <span className="text-yellow-400">Checking...</span>;
      case "connected":
        return <span className="text-green-400">✓ Connected</span>;
      case "failed":
        return <span className="text-red-400">✗ Failed</span>;
      default:
        return <span className="text-yellow-400">Unknown</span>;
    }
  };

  const handleStartNewGame = () => {
    setGameState("character-creation");
  };

  const handleCharacterCreate = async () => {
    if (!characterName.trim()) return;

    try {
      // Create character in backend
      const response = await fetch("http://localhost:8001/character/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: characterName,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setCharacter(data.character);

        // Initialize game session with this character
        await initializeGame({
          name: characterName,
        });

        setGameState("game");
      }
    } catch (error) {
      console.error("Failed to create character:", error);
    }
  };

  const handleCommandExecute = async (command: string) => {
    executeCommand(command); // WebSocket sends immediately, no await needed
  };

  const handleExitGame = () => {
    if (confirm("Are you sure you want to exit? Your progress will be lost.")) {
      // Reset state manually since WebSocket hook doesn't have resetGame
      setGameState("main");
      setCharacter(null);
      setCharacterName("");
      window.location.reload(); // Simple way to reset all state including WebSocket
    }
  };

  const handleSaveGame = async (sessionName: string) => {
    if (!session) {
      throw new Error("No active game session");
    }

    try {
      await saveGame(session.game_id, sessionName);
    } catch (error) {
      console.error("Failed to save game:", error);
      throw error;
    }
  };

  const handleLoadGame = async (gameId: string) => {
    try {
      const result = await loadGame(gameId);

      // Load existing game session (don't create new one)
      loadGameSession(result.game_id, result.session);

      // Set character and navigate to game screen
      setCharacter(result.session.character);
      setShowLoadModal(false);
      setGameState("game");
    } catch (error) {
      console.error("Failed to load game:", error);
      throw error;
    }
  };

  const handleDeleteSave = async (gameId: string) => {
    try {
      await deleteSavedGame(gameId);
    } catch (error) {
      console.error("Failed to delete save:", error);
      throw error;
    }
  };

  const handleFetchSaves = async () => {
    try {
      const result = await listSavedGames();
      return result.saves;
    } catch (error) {
      console.error("Failed to fetch saves:", error);
      throw error;
    }
  };

  const renderMainScreen = () => (
    <div className="text-center">
      <h1 className="text-4xl font-bold mb-8">ADVENTURE ENGINE</h1>
      <div className="max-w-2xl text-left">
        <p className="mb-4">&gt; Initializing Adventure Engine...</p>
        <p className="mb-4">&gt; Loading multi-agent system...</p>
        <p className="mb-4">&gt; Connecting to vector database...</p>
        <p className="mb-8">&gt; Ready for adventure!</p>

        <div className="border border-green-400 p-4 mb-4">
          <h2 className="text-xl mb-2">System Status</h2>
          <p>&gt; Backend API: {getStatusDisplay()}</p>
          <p>
            &gt; Agents Active:{" "}
            <span className="text-green-400">
              IntentParser, AdventureNarrator, RoomDescriptor, InventoryManager
            </span>
          </p>
          <p>
            &gt; Vector Store:{" "}
            <span className="text-green-400">5 rooms + 5 items (ChromaDB)</span>
          </p>
        </div>

        <div className="border border-green-400 p-4 mb-4">
          <h2 className="text-xl mb-2">Available Commands</h2>
          <button
            onClick={handleStartNewGame}
            className="block w-full text-left hover:bg-green-400 hover:text-black p-2"
            disabled={backendStatus !== "connected"}
          >
            &gt; START - Begin new adventure
          </button>
          <button
            onClick={() => setShowLoadModal(true)}
            className="block w-full text-left hover:bg-green-400 hover:text-black p-2"
            disabled={backendStatus !== "connected"}
          >
            &gt; LOAD - Continue saved game
          </button>
          <p className="p-2 text-gray-500">
            &gt; HELP - Show all commands (Coming soon)
          </p>
        </div>
      </div>
    </div>
  );

  const renderCharacterCreation = () => (
    <div className="text-center max-w-2xl">
      <h1 className="text-4xl font-bold mb-8">CREATE YOUR ADVENTURER</h1>

      <div className="border border-green-400 p-4 mb-8">
        <h3 className="text-2xl font-bold mb-2">ADVENTURER</h3>
        <p className="mb-4">
          A brave explorer seeking fortune and glory in the legendary Cave of
          Echoing Depths
        </p>
      </div>

      <div className="mb-8">
        <label className="block mb-2 text-lg">Enter your name:</label>
        <input
          type="text"
          value={characterName}
          onChange={(e) => setCharacterName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && characterName.trim()) {
              handleCharacterCreate();
            }
          }}
          placeholder="Your adventurer's name"
          className="bg-black border border-green-400 text-green-400 p-2 w-full max-w-md"
          maxLength={20}
          autoFocus
        />
      </div>

      <div className="space-x-4">
        <button
          onClick={handleCharacterCreate}
          disabled={!characterName.trim()}
          className="px-6 py-2 bg-green-400 text-black disabled:bg-gray-600 disabled:text-gray-400"
        >
          Begin Adventure
        </button>
        <button
          onClick={() => setGameState("main")}
          className="px-6 py-2 border border-green-400 hover:bg-green-400 hover:text-black"
        >
          Back to Main Menu
        </button>
      </div>
    </div>
  );

  const renderGameScreen = () => {
    if (!session) {
      return (
        <div className="text-center">
          <p className="text-yellow-400">Loading game session...</p>
        </div>
      );
    }

    return (
      <GameScreen
        session={session}
        narrative={narrative}
        isLoading={isLoading}
        isTyping={isTyping}
        isConnected={isConnected}
        onCommand={handleCommandExecute}
        onExit={handleExitGame}
        onSave={handleSaveGame}
        onLoad={handleLoadGame}
        onDelete={handleDeleteSave}
        onFetchSaves={handleFetchSaves}
      />
    );
  };

  const renderCurrentScreen = () => {
    switch (gameState) {
      case "main":
        return renderMainScreen();
      case "character-creation":
        return renderCharacterCreation();
      case "game":
        return renderGameScreen();
      default:
        return renderMainScreen();
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-black text-green-400 font-mono">
      {renderCurrentScreen()}

      {/* Load Game Modal (available from main menu) */}
      <LoadGameModal
        isOpen={showLoadModal}
        onClose={() => setShowLoadModal(false)}
        onLoad={handleLoadGame}
        onDelete={handleDeleteSave}
        onFetchSaves={handleFetchSaves}
      />
    </main>
  );
}
