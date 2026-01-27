"""FastAPI adventure engine with character classes and Redis session management."""
import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
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

# Import database models and session
from app.db import get_db, init_db
from app.models.database import (
    Character as DBCharacter,
    GameSession as DBGameSession,
    Discovery
)

# Import game mechanics
from app.mechanics import (
    GameStatus,
    initialize_game_mechanics,
    update_game_status
)

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Simplified character model - classes are cosmetic only
class CharacterCreationRequest(BaseModel):
    """Request model for creating a new character."""
    name: str
    character_class: Optional[str] = "adventurer"  # Cosmetic only, no stat differences

class GameCommand(BaseModel):
    """Game command model for player actions."""
    command: str
    parameters: Optional[Dict] = None

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
adventure_narrator = AdventureNarrator(
    room_descriptor=room_descriptor,
    inventory_manager=inventory_manager
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

@app.post("/character/create")
async def create_character(request: CharacterCreationRequest):
    """Create a new character"""
    character = {
        "name": request.name,
        "character_class": "adventurer",
        "level": 1
    }

    return {
        "character": character,
        "message": f"Created adventurer '{request.name}' successfully!"
    }

@app.post("/game/start")
async def start_game(request: CharacterCreationRequest):
    """Start a new game session for the provided character info"""
    # Build character payload (character_class is cosmetic only)
    character = {
        "name": request.name,
        "character_class": request.character_class or "adventurer",
        "level": 1,
        "hp": 20
    }

    session = await create_session(character)

    # Create introduction narrative
    intro_narrative = f"""
**Welcome, {character['name']}!**

You stand at the entrance to the legendary Cave of Echoing Depths, a place whispered about in tavern tales and ancient scrolls. Deep within these caverns lies the **Crystal of Echoing Depths**, an artifact of immense power said to contain the wisdom of forgotten civilizations.

Your quest is simple but perilous: **retrieve the crystal and escape the cave alive**.

The previous explorer who sought this treasure left behind equipment and notes but never returned. Their journal may hold crucial warnings about what lies ahead.

Type 'look around' to survey your surroundings, or dive straight in with commands like 'go north' to explore.

**Your adventure begins now...**
"""

    return {
        "game_id": session["game_id"],
        "session": session,
        "intro_narrative": intro_narrative
    }


async def _process_game_command_internal(game_id: str, command_text: str, parameters: Optional[Dict] = None):
    """Internal helper to process a game command. Shared by REST API and WebSocket.

    Args:
        game_id: The game session ID
        command_text: The command text from the player
        parameters: Optional command parameters

    Returns:
        Tuple of (session, game_response, full_narrative) or (None, None, error_dict) on error
    """
    session = await get_session(game_id)
    if not session:
        return None, None, {"error": "session_not_found", "message": "Game session not found"}

    # Initialize game mechanics if not present (for backward compatibility)
    initialize_game_mechanics(session)

    # Update session state
    session.setdefault("turn_count", 0)
    session["turn_count"] += 1
    session.setdefault("location", "cave_entrance")
    session.setdefault("inventory", [])
    session.setdefault("visited_rooms", [])

    # DEBUG: Log current inventory state
    logger.info("SESSION LOADED - Game: %s, Turn: %s, Inventory: %s, Location: %s, temp_flags: %s",
                game_id, session['turn_count'], session.get('inventory', []),
                session.get('location'), session.get('temp_flags', {}))

    # Record command in history
    history = session.setdefault("history", [])
    history.append({"turn": session["turn_count"], "command": command_text, "params": parameters})

    # Parse command using AdventureNarrator (AI-powered intent classification)
    parsed_command = await adventure_narrator.parse_command(command_text, parameters)

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
            "turns_since_collapse": session.get("turns_since_collapse", 0),
            "temp_flags": session.get("temp_flags", {})
        }
    )

    # Apply game state updates from agent response
    if game_response.game_state_updates:
        logger.info("APPLYING UPDATES: %s", game_response.game_state_updates)
        for key, value in game_response.game_state_updates.items():
            # Special handling for temp_flags - merge instead of replace
            if key == 'temp_flags' and isinstance(value, dict):
                if 'temp_flags' not in session:
                    session['temp_flags'] = {}
                session['temp_flags'].update(value)
            else:
                session[key] = value

    # DEBUG: Log inventory and temp_flags after updates
    logger.info("SESSION AFTER UPDATES - Inventory: %s, Location: %s, temp_flags: %s",
                session.get('inventory', []), session.get('location'), session.get('temp_flags', {}))

    # Use the narrative from the agent response
    full_narrative = game_response.narrative

    # Check for victory or defeat conditions
    # Skip if the command itself just set the game_status (to avoid duplicate narratives)
    if 'game_status' not in game_response.game_state_updates:
        status_narrative = update_game_status(session)
        if status_narrative:
            # Game has ended (victory or defeat)
            full_narrative = f"{full_narrative}\n{status_narrative}"

    # Save the updated session
    await save_session(game_id, session)

    return session, game_response, full_narrative


@app.post("/game/{game_id}/command")
async def process_command(game_id: str, command: GameCommand):
    """Process a command within an active game session using AI agents.

    Loads the session, parses the command through AdventureNarrator,
    coordinates with specialist agents (RoomDescriptor, InventoryManager),
    and returns a rich narrative response with updated game state.
    """
    try:
        session, game_response, full_narrative = await _process_game_command_internal(
            game_id, command.command, command.parameters
        )

        if session is None:
            # Error occurred (result contains error dict)
            return full_narrative

        return {
            "game_id": game_id,
            "turn": session["turn_count"],
            "response": full_narrative,
            "agent": game_response.agent,
            "success": game_response.success,
            "session": session,
            "metadata": game_response.metadata,
            "game_status": session.get("status", GameStatus.IN_PROGRESS)
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

            try:
                # Send typing indicator
                await websocket.send_json({
                    "type": "typing",
                    "agent": "adventure_narrator"
                })

                # Process command using shared internal function
                # This ensures WebSocket and REST API have identical behavior
                session, game_response, full_narrative = await _process_game_command_internal(
                    game_id, command_text, parameters
                )

                if session is None:
                    # Error occurred (full_narrative contains error dict)
                    await websocket.send_json({
                        "type": "error",
                        "error": full_narrative.get("error", "unknown_error"),
                        "message": full_narrative.get("message", "An error occurred")
                    })
                    continue

                # Stream the narrative response in chunks (word-by-word for dramatic effect)
                # NOTE: This is "fake streaming" - we already have the full response
                # Real streaming would send tokens as the LLM generates them
                words = full_narrative.split()

                for i, word in enumerate(words):
                    # Add space between words (except for first word)
                    chunk = word if i == 0 else f" {word}"
                    chunk_msg = {
                        "type": "chunk",
                        "data": chunk
                    }
                    await websocket.send_json(chunk_msg)
                    # Small delay to create streaming effect (adjust for desired speed)
                    await asyncio.sleep(0.04)  # 40ms between words = ~25 words/second

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


@app.post("/game/{game_id}/save")
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
