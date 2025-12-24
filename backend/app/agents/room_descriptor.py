"""Room Descriptor Agent - Specialist for room descriptions and environmental details."""
import os
from typing import Dict, Any, Optional, List
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

# Import RAG tools
from app.tools.rag_tools import query_world_lore, get_room_description as rag_get_room_description

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
    async def get_room_features(ctx: RunContext[RoomContext], location: str) -> str:  # pylint: disable=unused-argument
        """Get additional environmental features for a location."""
        # TODO: Query vector store (Chroma) for location-specific features
        return f"Environmental features for {location} would come from vector store."


    async def check_room_connections(
            ctx: RunContext[RoomContext],
            from_location: str, direction: str) -> Dict[str, Any]:
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
        tools=[get_room_features, check_room_connections],  # pylint: disable=possibly-used-before-assignment
    )
else:
    ROOM_DESCRIPTOR_AGENT = None


# Room connection map based on world_config.md
ROOM_CONNECTIONS = {
    "cave_entrance": {
        "north": "hidden_alcove",
        "east": "yawning_chasm"
    },
    "hidden_alcove": {
        "south": "cave_entrance"
    },
    "yawning_chasm": {
        "west": "cave_entrance",
        "east": "crystal_treasury",
        "south": "collapsed_passage"
    },
    "crystal_treasury": {
        "west": "yawning_chasm"
    },
    "collapsed_passage": {
        "north": "yawning_chasm"
    }
}


class RoomDescriptor:
    """Wrapper class for the room descriptor agent.

    Provides compatibility with existing code while using PydanticAI underneath when available.
    Uses RAG to retrieve rich room descriptions from the vector database.
    """

    def __init__(self):
        """Initialize the RoomDescriptor with default context."""
        self.context = RoomContext(
            current_location="Cave Entrance",
            room_connections=ROOM_CONNECTIONS
        )

    async def get_room_description(self, location: str) -> str:
        """
        Get a description for the specified location using RAG.

        Args:
            location: Room name in human-readable format (e.g., "Cave Entrance")
                     Will be automatically normalized for RAG queries

        Returns:
            Rich description of the room
        """
        self.context.current_location = location
        if location not in self.context.visited_rooms:
            self.context.visited_rooms.append(location)  # pylint: disable=no-member

        # RAG query automatically normalizes location names (Cave Entrance -> cave_entrance)
        rag_description = rag_get_room_description(location)

        # If we got substantial content from RAG, use it
        if rag_description and len(rag_description) > 50:
            return rag_description

        # If PydanticAI agent is available and OpenAI key is set, use it
        if PYDANTIC_AI_AVAILABLE and ROOM_DESCRIPTOR_AGENT:
            try:
                result = await ROOM_DESCRIPTOR_AGENT.run(
                    f"Describe the {location} in an evocative way",
                    deps=self.context
                )
                return result.data
            except Exception:
                # Fallback if AI call fails
                pass

        # Final fallback
        return rag_description if rag_description else f"You are in {location}."

    async def handle_movement(self, from_location: str, direction: str) -> Dict[str, Any]:
        """Handle movement between rooms using the room connection map."""
        # Check if movement is valid
        connections = ROOM_CONNECTIONS.get(from_location, {})

        if direction in connections:
            new_location = connections[direction]
            description = await self.get_room_description(new_location)

            return {
                "success": True,
                "new_location": new_location,
                "description": f"You move {direction}.\n\n{description}"
            }

        # Invalid direction
        available_directions = list(connections.keys()) if connections else []
        if available_directions:
            dirs_text = ", ".join(available_directions)
            blocked_msg = f"You can't go {direction} from here. Available directions: {dirs_text}."
        else:
            blocked_msg = f"You can't go {direction} from here. There are no obvious exits."

        return {
            "success": False,
            "new_location": from_location,
                "description": blocked_msg,
                "blocked_reason": f"No exit {direction}"
            }

    async def examine_environment(
            self, location: str,
            target: str = None, inventory: List[str] = None) -> str:
        """Examine environmental details in a room using RAG.
        
        Args:
            location: Current room location
            target: Specific thing to examine (or None for general look)
            inventory: Player's current inventory to filter out picked-up items
        """
        self.context.current_location = location
        inventory = inventory or []

        # Query RAG for specific details about the target or general environment
        if target:
            # Try multiple query strategies to find content about the target
            queries = [
                f"{target}",  # Direct match
                f"{target} description details",
                f"{target} symbols carvings",  # For carvings/symbols
            ]

            all_results = []
            for query in queries:
                results = query_world_lore(query, location, max_results=3)
                if results:
                    all_results.extend(results)

            if all_results:
                # Filter out bullet points, headers, and metadata
                substantive_results = []

                for result in all_results:
                    if not result or len(result) < 20:
                        continue

                    # Check if this result is actually about the target
                    target_words = target.lower().split()
                    relevance = sum(1 for word in target_words
                                    if word in result.lower())

                    if relevance == 0:
                        continue

                    # Split into sentences to find focused content
                    sentences = result.replace('\n', ' ').split('.')
                    focused_sentences = []

                    for sentence in sentences:
                        sentence = sentence.strip()
                        # Skip bullets, headers, or metadata
                        if (sentence.startswith('-') or
                                sentence.startswith('#') or
                                ':**' in sentence or
                                len(sentence) < 15):
                            continue

                        # Check if sentence is about the target
                        sentence_lower = sentence.lower()
                        target_lower = target.lower()
                        if any(word in sentence_lower
                               for word in target_words):
                            # Avoid sentences mentioning multiple items
                            items = ['rope', 'torch', 'pack', 'potion',
                                     'gear', 'journal']
                            item_mentions = sum(
                                1 for word in items
                                if word in sentence_lower and
                                word not in target_lower
                            )

                            # Only include if focuses on target
                            if item_mentions <= 1:
                                focused_sentences.append(sentence)

                    if focused_sentences:
                        cleaned_text = '. '.join(focused_sentences) + '.'
                        substantive_results.append((relevance, cleaned_text))

                if substantive_results:
                    # Return the most relevant match
                    substantive_results.sort(reverse=True, key=lambda x: x[0])
                    return substantive_results[0][1]
        else:
            # General examination - get main room description, not atmospheric details
            return await self.get_room_description(location)

        # If no RAG results, return a reasonable "not found" message instead of generic AI response
        if target:
            return f"You don't see anything particularly notable about {target} here."
        return f"You look around {location} but don't notice anything unusual."
