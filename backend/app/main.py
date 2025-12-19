"""FastAPI adventure engine with character classes and Redis session management."""
import json
import os
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis.asyncio as aioredis

# Load environment variables
load_dotenv()

# Character class definitions
class CharacterClass(str, Enum):
    """Available character classes with different stat distributions."""
    WARRIOR = "warrior"
    WIZARD = "wizard"
    ROGUE = "rogue"

class Stats(BaseModel):
    """Character statistics model."""
    strength: int
    magic: int
    agility: int
    health: int
    stealth: int

class Character(BaseModel):
    """Character model with class and stats."""
    name: str
    character_class: CharacterClass
    stats: Stats
    level: int = 1

class CharacterCreationRequest(BaseModel):
    """Request model for creating a new character."""
    name: str
    character_class: CharacterClass

class GameCommand(BaseModel):
    """Game command model for player actions."""
    command: str
    parameters: Optional[Dict] = None

# Class stat templates
CLASS_STATS = {
    CharacterClass.WARRIOR: Stats(
        strength=15,
        magic=5,
        agility=10,
        health=20,
        stealth=5
    ),
    CharacterClass.WIZARD: Stats(
        strength=5,
        magic=18,
        agility=8,
        health=12,
        stealth=7
    ),
    CharacterClass.ROGUE: Stats(
        strength=8,
        magic=6,
        agility=17,
        health=10,
        stealth=16
    )
}

app = FastAPI(
    title="Adventure Engine API",
    description="Multi-agent text adventure game engine",
    version="0.1.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis client (uses REDIS_URL env or defaults to localhost)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)


async def create_session(character: dict) -> dict:
    """Create a new game session with the given character."""
    game_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat() + "Z"
    session = {
        "game_id": game_id,
        "created_at": now,
        "updated_at": now,
        "character": character,
        "location": "dungeon_entrance",
        "inventory": [],
        "discovered": ["dungeon_entrance"],
        "turn_count": 0,
        "temp_flags": {}
    }
    await redis_client.set(f"session:{game_id}", json.dumps(session))
    return session


async def get_session(game_id: str) -> Optional[dict]:
    """Retrieve a game session from Redis."""
    data = await redis_client.get(f"session:{game_id}")
    if not data:
        return None
    return json.loads(data)


async def save_session(game_id: str, session: dict):
    """Save a game session to Redis."""
    session["updated_at"] = datetime.utcnow().isoformat() + "Z"
    await redis_client.set(f"session:{game_id}", json.dumps(session))

@app.get("/")
async def root():
    """Root endpoint showing API status and service connectivity."""
    return {
        "message": "Adventure Engine API is running!",
        "status": "operational",
        "services": {
            "database": "connected" if os.getenv("DATABASE_URL") else "not configured",
            "redis": "connected" if os.getenv("REDIS_URL") else "not configured",
            "chroma": "connected" if os.getenv("CHROMA_URL") else "not configured",
            "openai": "configured" if os.getenv("OPENAI_API_KEY") else "not configured"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {"status": "healthy"}

@app.get("/character/classes")
async def get_character_classes():
    """Get available character classes with their stat templates"""
    return {
        "classes": {
            CharacterClass.WARRIOR: {
                "name": "Warrior",
                "description": "Strong and resilient fighter, excels in combat and "
                              "physical challenges",
                "stats": CLASS_STATS[CharacterClass.WARRIOR].model_dump(),
                "strengths": ["Combat", "Breaking obstacles", "High health", 
                             "Intimidation"]
            },
            CharacterClass.WIZARD: {
                "name": "Wizard",
                "description": "Master of arcane arts, solves problems with magic "
                              "and intellect",
                "stats": CLASS_STATS[CharacterClass.WIZARD].model_dump(),
                "strengths": ["Magic spells", "Ancient knowledge", "Puzzle solving",
                             "Enchanted items"]
            },
            CharacterClass.ROGUE: {
                "name": "Rogue",
                "description": "Sneaky and agile, masters of stealth and precision",
                "stats": CLASS_STATS[CharacterClass.ROGUE].model_dump(),
                "strengths": ["Stealth", "Lockpicking", "Trap detection",
                             "Agility challenges"]
            }
        }
    }

@app.post("/character/create")
async def create_character(request: CharacterCreationRequest):
    """Create a new character with the specified class"""
    character = Character(
        name=request.name,
        character_class=request.character_class,
        stats=CLASS_STATS[request.character_class]
    )

    # NOTE: Character saved to Redis session when game starts
    return {
        "character": character.model_dump(),
        "message": f"Created {request.character_class.value} '{request.name}' "
                   f"successfully!"
    }

@app.get("/character/stats/{character_class}")
async def get_class_stats(character_class: CharacterClass):
    """Get stat breakdown for a specific character class"""
    return {
        "class": character_class.value,
        "stats": CLASS_STATS[character_class].model_dump()
    }

@app.post("/game/start")
async def start_game(request: CharacterCreationRequest):
    """Start a new game session for the provided character info"""
    # Build character payload
    character = {
        "name": request.name,
        "character_class": request.character_class.value,
        "stats": CLASS_STATS[request.character_class].model_dump(),
        "level": 1
    }

    # initialize HP from stats
    character["hp"] = character["stats"].get("health", 10)

    session = await create_session(character)
    return {"game_id": session["game_id"], "session": session}


@app.post("/game/{game_id}/command")
async def process_command(game_id: str, command: GameCommand):
    """Process a command within an active game session.

    This is a lightweight stub that loads the Redis session, increments
    the turn counter, appends the command to a simple history, and
    returns a placeholder response. Later this will delegate to the
    GameSessionManager and AdventureNarrator agents.
    """
    session = await get_session(game_id)
    if not session:
        return {"error": "session_not_found", "message": "Game session not found"}

    # Basic command handling stub: increment turn count and record command
    session.setdefault("turn_count", 0)
    session["turn_count"] += 1
    history = session.setdefault("history", [])
    history.append({"turn": session["turn_count"], "command": command.command,
                   "params": command.parameters})

    # Save the updated session
    await save_session(game_id, session)

    # Placeholder response
    response_text = f"Received command '{command.command}'. (Command processing not yet implemented.)"

    return {
        "game_id": game_id,
        "turn": session["turn_count"],
        "response": response_text,
        "session": session
    }


@app.get("/game/{game_id}/state")
async def get_game_state(game_id: str):
    """Get the current state of a game session."""
    session = await get_session(game_id)
    if not session:
        return {"error": "session_not_found", "message": "Game session not found"}
    return session
