"""FastAPI adventure engine with character classes and Redis session management."""
import asyncio
import json
import os
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Import adventure agents
from app.agents.adventure_narrator import AdventureNarrator
from app.agents.room_descriptor import RoomDescriptor
from app.agents.inventory_manager import InventoryManager
from app.agents.entity_manager import EntityManager

# Import database models and session
from app.db import get_db, init_db
from app.models.database import (
    Character as DBCharacter,
    GameSession as DBGameSession,
    Discovery
)

# Import game mechanics
from app.mechanics import (
    CollapseManager,
    DamageSystem,
    GameStatus,
    initialize_game_mechanics,
    should_trigger_collapse,
    update_game_status
)

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

# Initialize adventure agents
room_descriptor = RoomDescriptor()
inventory_manager = InventoryManager()
entity_manager = EntityManager()
adventure_narrator = AdventureNarrator(
    room_descriptor=room_descriptor,
    inventory_manager=inventory_manager,
    entity_manager=entity_manager
)


async def create_session(character: dict) -> dict:
    """Create a new game session with the given character."""
    game_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat() + "Z"
    session = {
        "game_id": game_id,
        "created_at": now,
        "updated_at": now,
        "character": character,
        "location": "cave_entrance",  # Start at the adventure's beginning
        "inventory": [],
        "discovered": ["cave_entrance"],
        "turn_count": 0,
        "temp_flags": {}
    }

    # Initialize game mechanics (collapse system, status, etc.)
    initialize_game_mechanics(session)

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
    """Process a command within an active game session using AI agents.

    Loads the session, parses the command through AdventureNarrator,
    coordinates with specialist agents (RoomDescriptor, InventoryManager, EntityManager),
    and returns a rich narrative response with updated game state.
    """
    session = await get_session(game_id)
    if not session:
        return {"error": "session_not_found", "message": "Game session not found"}

    # Initialize game mechanics if not present (for backward compatibility)
    initialize_game_mechanics(session)

    # Update session state
    session.setdefault("turn_count", 0)
    session["turn_count"] += 1
    session.setdefault("location", "cave_entrance")
    session.setdefault("inventory", [])
    session.setdefault("visited_rooms", [])

    # Record command in history
    history = session.setdefault("history", [])
    history.append({"turn": session["turn_count"], "command": command.command,
                   "params": command.parameters})

    # Increment collapse turn counter if collapse is active BEFORE command processing
    collapse_was_active = CollapseManager.is_collapse_active(session)
    if collapse_was_active:
        CollapseManager.increment_collapse_turn(session)

    # Apply environmental damage during collapse (before command)
    damage_result = DamageSystem.apply_environmental_damage(session)
    damage_narrative = damage_result.get("narrative", "")

    try:
        # Parse command using AdventureNarrator
        parsed_command = adventure_narrator.parse_command(command.command, command.parameters)

        # Process command through agent coordination
        character = session.get("character", {})
        character_class = character.get("character_class", "") if isinstance(character, dict) else ""
        game_response = await adventure_narrator.handle_command(
            parsed_command=parsed_command,
            game_state={
                "location": session["location"],
                "inventory": session["inventory"],
                "visited_rooms": session["visited_rooms"],
                "character": character,
                "character_class": character_class,
                "turn_count": session["turn_count"],
                "collapse_triggered": session.get("collapse_triggered", False),
                "turns_since_collapse": session.get("turns_since_collapse", 0)
            }
        )

        # Apply game state updates from agent response
        if game_response.game_state_updates:
            for key, value in game_response.game_state_updates.items():
                session[key] = value

        # Check if command should trigger collapse AFTER inventory is updated
        collapse_narrative = ""
        if should_trigger_collapse(command.command, session):
            collapse_narrative = CollapseManager.trigger_collapse(session)

        # Add collapse narrative if triggered or ongoing
        full_narrative = game_response.narrative
        if collapse_narrative:
            full_narrative = f"{game_response.narrative}\n\n{collapse_narrative}"
        elif CollapseManager.is_collapse_active(session):
            # Add ongoing collapse warnings
            collapse_warning = CollapseManager.get_collapse_narrative(session)
            if collapse_warning:
                full_narrative = f"{collapse_warning}\n\n{game_response.narrative}"

        # Add damage narrative if damage occurred
        if damage_narrative:
            full_narrative = f"{full_narrative}\n\n{damage_narrative}"

        # Check for victory or defeat conditions
        status_narrative = update_game_status(session)
        if status_narrative:
            # Game has ended (victory or defeat)
            full_narrative = f"{full_narrative}\n{status_narrative}"

        # Save the updated session
        await save_session(game_id, session)

        return {
            "game_id": game_id,
            "turn": session["turn_count"],
            "response": full_narrative,
            "agent": game_response.agent,
            "success": game_response.success,
            "session": session,
            "metadata": game_response.metadata,
            "game_status": session.get("status", GameStatus.ACTIVE)
        }

    except Exception as exc:
        # Fallback for any processing errors
        error_response = f"Error processing command '{command.command}': {str(exc)}"

        await save_session(game_id, session)

        return {
            "game_id": game_id,
            "turn": session["turn_count"],
            "response": error_response,
            "agent": "system",
            "success": False,
            "session": session,
            "error": str(exc)
        }


@app.get("/game/{game_id}/state")
async def get_game_state(game_id: str):
    """Get the current state of a game session."""
    session = await get_session(game_id)
    if not session:
        return {"error": "session_not_found", "message": "Game session not found"}
    return session


@app.websocket("/ws/game/{game_id}")
async def websocket_game_endpoint(websocket: WebSocket, game_id: str):
    """WebSocket endpoint for real-time game interaction with streaming responses.

    Connection flow:
    1. Client connects with game_id
    2. Server validates session exists
    3. Bi-directional communication begins:
       - Client sends: {"command": "look around", "parameters": {}}
       - Server streams: {"type": "chunk", "data": "You peer..."}
                        {"type": "chunk", "data": " into the..."}
                        {"type": "complete", "session": {...}}
    """
    await websocket.accept()

    # Validate session exists
    session = await get_session(game_id)
    if not session:
        await websocket.send_json({
            "type": "error",
            "error": "session_not_found",
            "message": "Game session not found"
        })
        await websocket.close()
        return

    # Send connection confirmation
    await websocket.send_json({
        "type": "connected",
        "game_id": game_id,
        "session": session
    })

    try:
        while True:
            # Receive command from client
            data = await websocket.receive_json()

            command_text = data.get("command", "")
            parameters = data.get("parameters")

            # Update session state
            session["turn_count"] = session.get("turn_count", 0) + 1
            session.setdefault("location", "cave_entrance")
            session.setdefault("inventory", [])
            session.setdefault("visited_rooms", [])

            # Record command in history
            history = session.setdefault("history", [])
            history.append({
                "turn": session["turn_count"],
                "command": command_text,
                "params": parameters
            })

            try:
                # Parse command using AdventureNarrator
                parsed_command = adventure_narrator.parse_command(command_text, parameters)

                # Send typing indicator
                await websocket.send_json({
                    "type": "typing",
                    "agent": "adventure_narrator"
                })

                # Process command through agent coordination with streaming
                # NOTE: Currently using handle_command which returns complete response
                # TODO: Implement streaming at the agent level for real LLM token streaming
                # This would require:
                # 1. RoomDescriptor/other agents to use agent.run_stream() instead of agent.run()
                # 2. AdventureNarrator to yield chunks as agents generate them
                # 3. Async generator pattern: async for chunk in narrator.handle_command_stream(...)

                character = session.get("character", {})
                character_class = character.get("character_class", "") if isinstance(character, dict) else ""

                game_response = await adventure_narrator.handle_command(
                    parsed_command=parsed_command,
                    game_state={
                        "location": session["location"],
                        "inventory": session["inventory"],
                        "visited_rooms": session["visited_rooms"],
                        "character": character,
                        "character_class": character_class,
                        "turn_count": session["turn_count"]
                    }
                )

                # Stream the narrative response in chunks (word-by-word for dramatic effect)
                # NOTE: This is "fake streaming" - we already have the full response
                # Real streaming would send tokens as the LLM generates them
                narrative = game_response.narrative
                words = narrative.split()

                for i, word in enumerate(words):
                    # Add space between words (except for first word)
                    chunk = word if i == 0 else f" {word}"
                    chunk_msg = {
                        "type": "chunk",
                        "data": chunk
                    }
                    await websocket.send_json(chunk_msg)
                    # Small delay to create streaming effect (adjust for desired speed)
                    await asyncio.sleep(0.08)  # 80ms between words = ~12 words/second

                # Apply game state updates from agent response
                if game_response.game_state_updates:
                    for key, value in game_response.game_state_updates.items():
                        session[key] = value

                # Save the updated session
                await save_session(game_id, session)

                # Send completion message with full state
                await websocket.send_json({
                    "type": "complete",
                    "game_id": game_id,
                    "turn": session["turn_count"],
                    "agent": game_response.agent,
                    "success": game_response.success,
                    "session": session,
                    "metadata": game_response.metadata
                })

            except Exception as exc:
                # Send error response
                error_message = f"Error processing command '{command_text}': {str(exc)}"

                await websocket.send_json({
                    "type": "error",
                    "message": error_message,
                    "error": str(exc)
                })

                await save_session(game_id, session)

    except WebSocketDisconnect:
        # Client disconnected - clean up if needed
        pass
    except Exception as exc:
        # Unexpected error - log and close
        await websocket.send_json({
            "type": "error",
            "message": f"WebSocket error: {str(exc)}"
        })
        await websocket.close()


# ============================================================================
# PERSISTENT SAVE/LOAD ENDPOINTS
# ============================================================================

class SaveGameRequest(BaseModel):
    """Request to save game to PostgreSQL."""
    session_name: Optional[str] = None


class SaveGameResponse(BaseModel):
    """Response after saving game."""
    game_id: str
    character_id: str
    session_name: str
    saved_at: str


@app.post("/game/{game_id}/save", response_model=SaveGameResponse)
async def save_game_to_database(
    game_id: str,
    request: SaveGameRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Save current game session to PostgreSQL for long-term persistence.

    This creates/updates:
    - Character record (if new)
    - GameSession record with full state
    - Discovery records for all discovered locations/items
    """
    # Get current session from Redis
    session = await get_session(game_id)
    if not session:
        return {"error": "session_not_found", "message": "Game session not found"}

    character_data = session.get("character", {})
    character_id = str(uuid.uuid4())

    # Check if character already exists in database
    result = await db.execute(
        select(DBCharacter).where(DBCharacter.name == character_data["name"])
    )
    existing_char = result.scalars().first()

    if existing_char:
        character_id = existing_char.id
        # Update character stats
        existing_char.level = character_data.get("level", 1)
        existing_char.stats = character_data.get("stats", {})
        existing_char.updated_at = datetime.utcnow()
    else:
        # Create new character
        new_character = DBCharacter(
            id=character_id,
            name=character_data["name"],
            character_class=character_data["character_class"],
            stats=character_data.get("stats", {}),
            level=character_data.get("level", 1)
        )
        db.add(new_character)

    # Create or update game session
    result = await db.execute(
        select(DBGameSession).where(DBGameSession.id == game_id)
    )
    existing_session = result.scalars().first()

    session_name = request.session_name or f"Adventure - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"

    if existing_session:
        # Update existing session
        existing_session.current_location = session.get("location", "cave_entrance")
        existing_session.inventory = session.get("inventory", [])
        existing_session.turn_count = session.get("turn_count", 0)
        existing_session.session_name = session_name
        existing_session.last_played = datetime.utcnow()
        existing_session.state_snapshot = session
    else:
        # Create new session record
        new_session = DBGameSession(
            id=game_id,
            character_id=character_id,
            current_location=session.get("location", "cave_entrance"),
            inventory=session.get("inventory", []),
            turn_count=session.get("turn_count", 0),
            session_name=session_name,
            is_active=True,
            state_snapshot=session
        )
        db.add(new_session)

    # Save discoveries
    discovered_rooms = session.get("discovered", [])
    for room_id in discovered_rooms:
        # Check if already recorded
        result = await db.execute(
            select(Discovery).where(
                Discovery.game_session_id == game_id,
                Discovery.entity_id == room_id
            )
        )
        if not result.scalars().first():
            discovery = Discovery(
                game_session_id=game_id,
                discovery_type="room",
                entity_id=room_id,
                display_name=room_id.replace("_", " ").title(),
                turn_number=session.get("turn_count", 0)
            )
            db.add(discovery)

    await db.commit()

    return SaveGameResponse(
        game_id=game_id,
        character_id=character_id,
        session_name=session_name,
        saved_at=datetime.utcnow().isoformat() + "Z"
    )


@app.get("/game/saves")
async def list_saved_games(db: AsyncSession = Depends(get_db)):
    """List all saved games from PostgreSQL."""
    result = await db.execute(
        select(DBGameSession, DBCharacter)
        .join(DBCharacter)
        .where(DBGameSession.is_active.is_(True))
        .order_by(DBGameSession.last_played.desc())
    )

    saves = []
    for session, character in result.all():
        saves.append({
            "game_id": session.id,
            "session_name": session.session_name,
            "character_name": character.name,
            "character_class": character.character_class,
            "level": character.level,
            "location": session.current_location,
            "turn_count": session.turn_count,
            "last_played": session.last_played.isoformat() + "Z" if session.last_played else None,
            "created_at": session.created_at.isoformat() + "Z" if session.created_at else None
        })

    return {"saves": saves, "count": len(saves)}


@app.post("/game/{game_id}/load")
async def load_game_from_database(
    game_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Load a saved game from PostgreSQL into Redis for active play.

    This restores:
    - Full session state
    - Character data
    - Discoveries
    """
    # Fetch session from database
    result = await db.execute(
        select(DBGameSession, DBCharacter)
        .join(DBCharacter)
        .where(DBGameSession.id == game_id)
    )
    row = result.first()

    if not row:
        return {"error": "save_not_found", "message": "Saved game not found"}

    db_session, db_character = row

    # Restore session to Redis
    session = db_session.state_snapshot or {
        "game_id": game_id,
        "character": {
            "name": db_character.name,
            "character_class": db_character.character_class,
            "stats": db_character.stats,
            "level": db_character.level
        },
        "location": db_session.current_location,
        "inventory": db_session.inventory or [],
        "turn_count": db_session.turn_count or 0,
        "discovered": [],
        "history": [],
        "temp_flags": {}
    }

    # Load discoveries
    result = await db.execute(
        select(Discovery)
        .where(Discovery.game_session_id == game_id)
        .where(Discovery.discovery_type == "room")
    )
    discoveries = result.scalars().all()
    session["discovered"] = [d.entity_id for d in discoveries]

    # Update timestamps
    session["created_at"] = db_session.created_at.isoformat() + "Z" if db_session.created_at else datetime.utcnow().isoformat() + "Z"
    session["updated_at"] = datetime.utcnow().isoformat() + "Z"

    # Save to Redis
    await redis_client.set(f"session:{game_id}", json.dumps(session))

    # Update last_played timestamp
    db_session.last_played = datetime.utcnow()
    await db.commit()

    return {
        "success": True,
        "game_id": game_id,
        "session": session,
        "message": f"Loaded save: {db_session.session_name}"
    }


@app.delete("/game/{game_id}/save")
async def delete_saved_game(
    game_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a saved game from PostgreSQL."""
    result = await db.execute(
        select(DBGameSession).where(DBGameSession.id == game_id)
    )
    session = result.scalars().first()

    if not session:
        return {"error": "save_not_found", "message": "Saved game not found"}

    # Mark as inactive instead of deleting (soft delete)
    session.is_active = False
    await db.commit()

    return {
        "success": True,
        "game_id": game_id,
        "message": "Save deleted successfully"
    }


# Initialize database tables on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables if they don't exist."""
    await init_db()
