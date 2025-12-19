"""Room Descriptor Agent - Specialist for room descriptions and environmental details."""
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

try:
    from pydantic_ai import Agent, RunContext
    from pydantic_ai.models.openai import OpenAIModel
    PYDANTIC_AI_AVAILABLE = True
except ImportError:
    # Fallback for testing or when PydanticAI is not available
    PYDANTIC_AI_AVAILABLE = False
    Agent = None
    RunContext = None

from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()


class RoomContext(BaseModel):
    """Context for room description agent."""
    current_location: str
    visited_rooms: list[str] = Field(default_factory=list)
    room_connections: Dict[str, Dict[str, str]] = Field(default_factory=dict)


class MovementResult(BaseModel):
    """Result of a movement action."""
    success: bool
    new_location: Optional[str] = None
    description: str
    blocked_reason: Optional[str] = None


# Tool functions (defined before agent creation)
if PYDANTIC_AI_AVAILABLE:
    async def get_room_features(ctx: RunContext[RoomContext], location: str) -> str:
        """Get additional environmental features for a location."""
        # TODO: Query vector store (Chroma) for location-specific features
        return f"Environmental features for {location} would come from vector store."


    async def check_room_connections(ctx: RunContext[RoomContext], from_location: str, direction: str) -> Dict[str, Any]:
        """Check if movement in a direction is valid."""
        # TODO: Implement actual room connection logic
        connections = ctx.deps.room_connections.get(from_location, {})
        if direction in connections:
            return {
                "valid": True,
                "destination": connections[direction],
                "description": f"You can go {direction} to {connections[direction]}."
            }
        return {
            "valid": False,
            "destination": None,
            "description": f"You cannot go {direction} from here."
        }


# Only create the agent if PydanticAI is available and OpenAI API key is set
if PYDANTIC_AI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
    # Create the RoomDescriptor agent with OpenAI model from environment
    model_name = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    ROOM_DESCRIPTOR_AGENT = Agent(
        model=OpenAIModel(model_name),
        result_type=str,
        system_prompt=(
            'You are a room description specialist for a text adventure game. '
            'Generate rich, immersive descriptions of locations with vivid details '
            'about atmosphere, lighting, objects, and notable features. '
            'Keep descriptions concise but evocative, around 2-3 sentences. '
            'Match the tone of classic text adventures like Zork.'
        ),
        deps_type=RoomContext,
        tools=[get_room_features, check_room_connections],
    )
else:
    ROOM_DESCRIPTOR_AGENT = None


class RoomDescriptor:
    """Wrapper class for the room descriptor agent.

    Provides compatibility with existing code while using PydanticAI underneath when available.
    """

    def __init__(self):
        """Initialize the RoomDescriptor with default context."""
        self.context = RoomContext(current_location="starting_room")

    async def get_room_description(self, location: str) -> str:
        """Get a description for the specified location."""
        self.context.current_location = location
        if location not in self.context.visited_rooms:
            self.context.visited_rooms.append(location)

        if PYDANTIC_AI_AVAILABLE and ROOM_DESCRIPTOR_AGENT:
            try:
                result = await ROOM_DESCRIPTOR_AGENT.run(
                    f"Describe the {location}",
                    deps=self.context
                )
                return result.data
            except Exception:
                # Fallback if AI call fails
                pass

        # Fallback implementation
        return f"You are in {location}. This room description will be enhanced with AI-generated content."

    async def handle_movement(self, from_location: str, direction: str) -> Dict[str, Any]:
        """Handle movement between rooms."""
        # Simple fallback logic
        new_location = f"{from_location}_{direction}"
        return {
            "success": True,
            "new_location": new_location,
            "description": f"You move {direction} to {new_location}."
        }

    async def examine_environment(self, location: str, target: str = None) -> str:
        """Examine environmental details in a room."""
        self.context.current_location = location

        if PYDANTIC_AI_AVAILABLE and ROOM_DESCRIPTOR_AGENT:
            try:
                if target:
                    prompt = f"Describe examining {target} in detail in the {location}"
                else:
                    prompt = f"Provide a detailed examination of the {location}, noting all visible features"

                result = await ROOM_DESCRIPTOR_AGENT.run(prompt, deps=self.context)
                return result.data
            except Exception:
                # Fallback if AI call fails
                pass

        # Fallback implementation
        if target:
            return f"You examine {target} in {location}. [Detailed examination coming soon]"
        return f"Looking around {location}, you see... [Environmental details coming soon]"
