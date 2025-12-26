"use client";

import { useState, useEffect } from "react";
import { useGameWebSocket } from "@/hooks/useGameWebSocket";
import { GameScreen } from "@/components/GameScreen";

interface CharacterClass {
  name: string;
  description: string;
  stats: {
    strength: number;
    magic: number;
    agility: number;
    health: number;
    stealth: number;
  };
  strengths: string[];
}

interface CharacterClasses {
  [key: string]: CharacterClass;
}

interface Character {
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

type GameState = "main" | "character-selection" | "character-creation" | "game";

export default function Home() {
  const [gameState, setGameState] = useState<GameState>("main");
  const [backendStatus, setBackendStatus] = useState<
    "checking" | "connected" | "failed"
  >("checking");
  const [characterClasses, setCharacterClasses] =
    useState<CharacterClasses | null>(null);
  const [selectedClass, setSelectedClass] = useState<string>("");
  const [characterName, setCharacterName] = useState<string>("");
  const [character, setCharacter] = useState<Character | null>(null);

  // Game state management hook with WebSocket
  const {
    session,
    narrative,
    isLoading,
    isTyping,
    isConnected,
    error: gameError,
    initializeGame,
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

    const loadCharacterClasses = async () => {
      try {
        const response = await fetch("http://localhost:8001/character/classes");
        if (response.ok) {
          const data = await response.json();
          setCharacterClasses(data.classes);
        }
      } catch (error) {
        console.error("Failed to load character classes:", error);
      }
    };

    checkBackendHealth();
    loadCharacterClasses();
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
    setGameState("character-selection");
  };

  const handleClassSelect = (classKey: string) => {
    setSelectedClass(classKey);
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
          character_class: selectedClass,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setCharacter(data.character);

        // Initialize game session with this character
        await initializeGame({
          name: characterName,
          character_class: selectedClass,
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
      setSelectedClass("");
      window.location.reload(); // Simple way to reset all state including WebSocket
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
              AdventureNarrator, RoomDescriptor, InventoryManager
            </span>
          </p>
          <p>
            &gt; Vector Store:{" "}
            <span className="text-green-400">52 content chunks loaded</span>
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
          <p className="p-2 text-gray-500">
            &gt; LOAD - Continue saved game (Coming soon)
          </p>
          <p className="p-2 text-gray-500">
            &gt; HELP - Show all commands (Coming soon)
          </p>
        </div>
      </div>
    </div>
  );

  const renderCharacterSelection = () => (
    <div className="text-center max-w-4xl">
      <h1 className="text-4xl font-bold mb-8">SELECT YOUR CLASS</h1>
      <p className="mb-8">&gt; Choose your path, adventurer...</p>

      {characterClasses && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(characterClasses).map(([key, classData]) => (
            <div
              key={key}
              className="border border-green-400 p-4 hover:bg-green-400 hover:text-black cursor-pointer"
              onClick={() => handleClassSelect(key)}
            >
              <h3 className="text-2xl font-bold mb-2">
                {classData.name.toUpperCase()}
              </h3>
              <p className="mb-4 text-sm">{classData.description}</p>

              <div className="text-left mb-4">
                <h4 className="text-lg font-bold mb-2">Stats:</h4>
                <p>Strength: {classData.stats.strength}</p>
                <p>Magic: {classData.stats.magic}</p>
                <p>Agility: {classData.stats.agility}</p>
                <p>Health: {classData.stats.health}</p>
                <p>Stealth: {classData.stats.stealth}</p>
              </div>

              <div className="text-left">
                <h4 className="text-sm font-bold mb-1">Strengths:</h4>
                {classData.strengths.map((strength, idx) => (
                  <p key={idx} className="text-xs">
                    • {strength}
                  </p>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <button
        onClick={() => setGameState("main")}
        className="mt-8 px-4 py-2 border border-green-400 hover:bg-green-400 hover:text-black"
      >
        Back to Main Menu
      </button>
    </div>
  );

  const renderCharacterCreation = () => (
    <div className="text-center max-w-2xl">
      <h1 className="text-4xl font-bold mb-8">CREATE CHARACTER</h1>

      {characterClasses && selectedClass && (
        <div className="border border-green-400 p-4 mb-8">
          <h3 className="text-2xl font-bold mb-2">
            {characterClasses[selectedClass].name.toUpperCase()}
          </h3>
          <p className="mb-4">{characterClasses[selectedClass].description}</p>

          <div className="grid grid-cols-2 gap-4 text-left">
            <div>
              <h4 className="font-bold mb-2">Base Stats:</h4>
              <p>Strength: {characterClasses[selectedClass].stats.strength}</p>
              <p>Magic: {characterClasses[selectedClass].stats.magic}</p>
              <p>Agility: {characterClasses[selectedClass].stats.agility}</p>
              <p>Health: {characterClasses[selectedClass].stats.health}</p>
              <p>Stealth: {characterClasses[selectedClass].stats.stealth}</p>
            </div>
            <div>
              <h4 className="font-bold mb-2">Class Features:</h4>
              {characterClasses[selectedClass].strengths.map(
                (strength, idx) => (
                  <p key={idx} className="text-sm">
                    • {strength}
                  </p>
                )
              )}
            </div>
          </div>
        </div>
      )}

      <div className="mb-8">
        <label className="block mb-2 text-lg">
          Enter your character's name:
        </label>
        <input
          type="text"
          value={characterName}
          onChange={(e) => setCharacterName(e.target.value)}
          placeholder="Your character's name"
          className="bg-black border border-green-400 text-green-400 p-2 w-full max-w-md"
          maxLength={20}
        />
      </div>

      <div className="space-x-4">
        <button
          onClick={handleCharacterCreate}
          disabled={!characterName.trim()}
          className="px-6 py-2 bg-green-400 text-black disabled:bg-gray-600 disabled:text-gray-400"
        >
          Create Character
        </button>
        <button
          onClick={() => setGameState("character-selection")}
          className="px-6 py-2 border border-green-400 hover:bg-green-400 hover:text-black"
        >
          Back to Classes
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
      />
    );
  };

  const renderCurrentScreen = () => {
    switch (gameState) {
      case "main":
        return renderMainScreen();
      case "character-selection":
        return renderCharacterSelection();
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
    </main>
  );
}
