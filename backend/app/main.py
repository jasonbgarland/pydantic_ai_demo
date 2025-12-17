from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

# Placeholder endpoints for game functionality
@app.post("/game/{game_id}/command")
async def process_command(game_id: str, command: dict):
    # TODO: Implement command processing with agents
    return {
        "game_id": game_id,
        "command": command,
        "response": "Command processing not yet implemented",
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