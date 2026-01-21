"""Entity Manager Agent - Specialist for NPCs, creatures, and interactive objects."""
import os
from typing import Dict, Any, List, Optional
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


class EntityContext(BaseModel):
    """Context for entity management."""
    current_location: str = "starting_room"
    entities_in_room: Dict[str, List[str]] = Field(default_factory=dict)
    entity_states: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class EntityInteraction(BaseModel):
    """Result of an entity interaction."""
    success: bool
    message: str
    dialogue: Optional[str] = None
    state_changes: Dict[str, Any] = Field(default_factory=dict)


# Tool functions (defined before agent creation)
if PYDANTIC_AI_AVAILABLE:
    async def get_entity_info(ctx: RunContext[EntityContext], entity_name: str) -> Dict[str, Any]:  # pylint: disable=unused-argument
        """Get information about an entity."""
        # TODO: Implement entity database lookup
        return {
            "name": entity_name,
            "type": "npc",
            "health": 100,
            "friendly": True,
            "description": f"A {entity_name}"
        }


    async def check_entity_presence(ctx: RunContext[EntityContext], entity_name: str, location: str) -> bool:
        """Check if an entity is present in a location."""
        entities = ctx.deps.entities_in_room.get(location, [])
        return entity_name in entities


    async def update_entity_state(ctx: RunContext[EntityContext], entity_name: str, state_update: Dict[str, Any]) -> bool:
        """Update the state of an entity."""
        if entity_name not in ctx.deps.entity_states:
            ctx.deps.entity_states[entity_name] = {}
        ctx.deps.entity_states[entity_name].update(state_update)
        return True


# Only create the agent if PydanticAI is available and OpenAI API key is set
if PYDANTIC_AI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
    # Create the EntityManager agent with OpenAI model from environment
    model_name = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    ENTITY_AGENT = Agent(
        model=OpenAIModel(model_name),
        output_type=EntityInteraction,
        system_prompt=(
            'You are an entity interaction specialist for a text adventure game. '
            'Handle conversations with NPCs, combat with creatures, and interactions with objects. '
            'Create engaging dialogue and realistic combat outcomes. '
            'Consider character stats, entity properties, and story context. '
            'Generate immersive responses that advance the narrative.'
        ),
        deps_type=EntityContext,
        tools=[get_entity_info, check_entity_presence, update_entity_state],  # pylint: disable=possibly-used-before-assignment
    )
else:
    ENTITY_AGENT = None


class EntityManager:
    """Wrapper class for the entity management agent.

    Provides compatibility with existing code while using PydanticAI underneath.
    """

    def __init__(self):
        """Initialize the EntityManager with default context."""
        self.context = EntityContext()

    async def talk_to_entity(self, entity_name: str) -> Dict[str, Any]:
        """Handle conversation with an NPC or entity."""
        if PYDANTIC_AI_AVAILABLE and ENTITY_AGENT:
            try:
                result = await ENTITY_AGENT.run(
                    f"Player wants to talk to: {entity_name}",
                    deps=self.context
                )
                return {
                    "success": result.output.success,
                    "message": result.output.message,
                    "dialogue": result.output.dialogue or f"{entity_name} says something interesting...",
                    "state_changes": result.output.state_changes
                }
            except Exception:
                # Fallback if AI call fails
                pass

        # Fallback implementation
        return {
            "success": True,
            "message": f"You talk to {entity_name}. [NPC dialogue system coming soon]",
            "dialogue": f"{entity_name} says something interesting...",
            "state_changes": {}
        }

    async def attack_entity(self, entity_name: str) -> Dict[str, Any]:
        """Handle combat with an entity."""
        if PYDANTIC_AI_AVAILABLE and ENTITY_AGENT:
            try:
                result = await ENTITY_AGENT.run(
                    f"Player attacks: {entity_name}",
                    deps=self.context
                )
                return {
                    "success": result.output.success,
                    "message": result.output.message,
                    "combat_result": "combat_in_progress" if result.output.success else "failed_attack",
                    "state_changes": result.output.state_changes
                }
            except Exception:
                # Fallback if AI call fails
                pass

        # Fallback implementation
        return {
            "success": True,
            "message": f"You attack the {entity_name}! [Combat system coming soon]",
            "combat_result": "placeholder_result",
            "state_changes": {}
        }

    async def interact_with_object(self, object_name: str, action: str) -> Dict[str, Any]:
        """Handle interaction with environmental objects."""
        if PYDANTIC_AI_AVAILABLE and ENTITY_AGENT:
            try:
                result = await ENTITY_AGENT.run(
                    f"Player wants to {action} the {object_name}",
                    deps=self.context
                )
                return {
                    "success": result.output.success,
                    "message": result.output.message,
                    "state_changes": result.output.state_changes
                }
            except Exception:
                # Fallback if AI call fails
                pass

        # Fallback implementation
        return {
            "success": True,
            "message": f"You {action} the {object_name}. [Object interaction coming soon]",
            "state_changes": {}
        }

    async def get_entities_in_location(self) -> List[str]:
        """Get a list of entities present in the current location."""
        return self.context.entities_in_room.get(self.context.current_location, [])  # pylint: disable=no-member

    async def check_entity_availability(self, entity_name: str) -> bool:
        """Check if an entity is available for interaction."""
        # TODO: Implement entity presence validation
        return bool(entity_name)  # Placeholder - assume all entities are available
