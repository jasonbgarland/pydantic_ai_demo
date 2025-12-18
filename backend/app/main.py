from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
from enum import Enum
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Character class definitions
class CharacterClass(str, Enum):
    WARRIOR = "warrior"
    WIZARD = "wizard"
    ROGUE = "rogue"

class Stats(BaseModel):
    strength: int
    magic: int
    agility: int
    health: int
    stealth: int

class Character(BaseModel):
    name: str
    character_class: CharacterClass
    stats: Stats
    level: int = 1

class CharacterCreationRequest(BaseModel):
    name: str
    character_class: CharacterClass

class GameCommand(BaseModel):
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

@app.get("/")
async def root():
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
    return {"status": "healthy"}

@app.get("/character/classes")
async def get_character_classes():
    """Get available character classes with their stat templates"""
    return {
        "classes": {
            CharacterClass.WARRIOR: {
                "name": "Warrior",
                "description": "Strong and resilient fighter, excels in combat and physical challenges",
                "stats": CLASS_STATS[CharacterClass.WARRIOR].dict(),
                "strengths": ["Combat", "Breaking obstacles", "High health", "Intimidation"]
            },
            CharacterClass.WIZARD: {
                "name": "Wizard", 
                "description": "Master of arcane arts, solves problems with magic and intellect",
                "stats": CLASS_STATS[CharacterClass.WIZARD].dict(),
                "strengths": ["Magic spells", "Ancient knowledge", "Puzzle solving", "Enchanted items"]
            },
            CharacterClass.ROGUE: {
                "name": "Rogue",
                "description": "Sneaky and agile, masters of stealth and precision",
                "stats": CLASS_STATS[CharacterClass.ROGUE].dict(), 
                "strengths": ["Stealth", "Lockpicking", "Trap detection", "Agility challenges"]
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
    
    # TODO: Save character to database
    return {
        "character": character.dict(),
        "message": f"Created {request.character_class.value} '{request.name}' successfully!"
    }

@app.get("/character/stats/{character_class}")
async def get_class_stats(character_class: CharacterClass):
    """Get stat breakdown for a specific character class"""
    return {
        "class": character_class.value,
        "stats": CLASS_STATS[character_class].dict()
    }

# Placeholder endpoints for game functionality
@app.post("/game/{game_id}/command")
async def process_command(game_id: str, command: GameCommand):
    # TODO: Implement command processing with agents
    # TODO: Load character for game_id to determine stat-based outcomes
    return {
        "game_id": game_id,
        "command": command.dict(),
        "response": "Command processing not yet implemented - will consider character stats",
        "agents_called": []
    }

@app.get("/game/{game_id}/state")
async def get_game_state(game_id: str):
    # TODO: Implement game state retrieval
    return {
        "game_id": game_id,
        "location": "starting_room",
        "inventory": [],
        "turn_count": 0,
        "message": "Game state not yet implemented"
    }