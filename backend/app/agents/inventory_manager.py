"""Inventory Manager Agent - Specialist for item interactions and inventory management."""
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


class InventoryContext(BaseModel):
    """Context for inventory management."""
    current_inventory: List[str] = Field(default_factory=list)
    inventory_limit: int = 10
    room_items: Dict[str, List[str]] = Field(default_factory=dict)


class ItemAction(BaseModel):
    """Result of an item action."""
    success: bool
    message: str
    inventory_update: List[str]
    room_update: Optional[Dict[str, List[str]]] = None


# Tool functions (defined before agent creation)
if PYDANTIC_AI_AVAILABLE:
    async def check_item_availability(ctx: RunContext[InventoryContext], item_name: str, location: str) -> bool:
        """Check if an item is available in the current location."""
        room_items = ctx.deps.room_items.get(location, [])
        return item_name in room_items


    async def validate_inventory_space(ctx: RunContext[InventoryContext]) -> bool:
        """Check if there's space in the inventory for another item."""
        return len(ctx.deps.current_inventory) < ctx.deps.inventory_limit


    async def get_item_properties(ctx: RunContext[InventoryContext], item_name: str) -> Dict[str, Any]:
        """Get properties and description of an item."""
        # TODO: Implement item database lookup
        return {
            "name": item_name,
            "description": f"A {item_name}",
            "usable": True,
            "value": 10
        }


# Only create the agent if PydanticAI is available and OpenAI API key is set
if PYDANTIC_AI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
    # Create the InventoryManager agent with OpenAI model from environment
    model_name = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    INVENTORY_AGENT = Agent(
        model=OpenAIModel(model_name),
        result_type=ItemAction,
        system_prompt=(
            'You are an inventory management specialist for a text adventure game. '
            'Handle item interactions with realistic constraints and provide '
            'engaging feedback for pickup, drop, and use actions. '
            'Consider inventory limits, item availability, and game logic. '
            'Generate responses that feel natural and immersive.'
        ),
        deps_type=InventoryContext,
        tools=[check_item_availability, validate_inventory_space, get_item_properties],
    )
else:
    INVENTORY_AGENT = None


class InventoryManager:
    """Wrapper class for the inventory management agent.

    Provides compatibility with existing code while using PydanticAI underneath.
    """

    def __init__(self):
        """Initialize the InventoryManager with empty inventory."""
        self.context = InventoryContext()

    async def pickup_item(self, item_name: str, current_inventory: List[str]) -> Dict[str, Any]:
        """Handle picking up an item."""
        self.context.current_inventory = current_inventory.copy()

        if PYDANTIC_AI_AVAILABLE and INVENTORY_AGENT:
            try:
                result = await INVENTORY_AGENT.run(
                    f"Player wants to pick up: {item_name}",
                    deps=self.context
                )
                return {
                    "success": result.data.success,
                    "message": result.data.message,
                    "inventory_update": result.data.inventory_update
                }
            except Exception:
                # Fallback if AI call fails
                pass

        # Fallback implementation
        new_inventory = current_inventory + [item_name]
        return {
            "success": True,
            "message": f"You pick up the {item_name}.",
            "inventory_update": new_inventory
        }

    async def drop_item(self, item_name: str, current_inventory: List[str]) -> Dict[str, Any]:
        """Handle dropping an item."""
        self.context.current_inventory = current_inventory.copy()

        if PYDANTIC_AI_AVAILABLE and INVENTORY_AGENT:
            try:
                result = await INVENTORY_AGENT.run(
                    f"Player wants to drop: {item_name}",
                    deps=self.context
                )
                return {
                    "success": result.data.success,
                    "message": result.data.message,
                    "inventory_update": result.data.inventory_update
                }
            except Exception:
                # Fallback if AI call fails
                pass

        # Fallback implementation
        if item_name in current_inventory:
            new_inventory = [item for item in current_inventory if item != item_name]
            return {
                "success": True,
                "message": f"You drop the {item_name}.",
                "inventory_update": new_inventory
            }
        return {
            "success": False,
            "message": f"You don't have a {item_name} to drop.",
            "inventory_update": current_inventory
        }

    async def use_item(self, item_name: str, current_inventory: List[str]) -> Dict[str, Any]:
        """Handle using an item."""
        self.context.current_inventory = current_inventory.copy()

        if PYDANTIC_AI_AVAILABLE and INVENTORY_AGENT:
            try:
                result = await INVENTORY_AGENT.run(
                    f"Player wants to use: {item_name}",
                    deps=self.context
                )
                return {
                    "success": result.data.success,
                    "message": result.data.message,
                    "inventory_update": result.data.inventory_update
                }
            except Exception:
                # Fallback if AI call fails
                pass

        # Fallback implementation
        if item_name in current_inventory:
            return {
                "success": True,
                "message": f"You use the {item_name}. [Item effects not yet implemented]",
                "inventory_update": current_inventory
            }
        return {
            "success": False,
            "message": f"You don't have a {item_name} to use.",
            "inventory_update": current_inventory
        }

    async def examine_item(self, item_name: str, current_inventory: List[str]) -> str:
        """Examine an item in detail."""
        self.context.current_inventory = current_inventory.copy()

        if item_name not in current_inventory:
            return f"You don't have a {item_name} to examine."

        if PYDANTIC_AI_AVAILABLE and INVENTORY_AGENT:
            try:
                result = await INVENTORY_AGENT.run(
                    f"Describe examining {item_name} in detail",
                    deps=self.context
                )
                return result.data.message
            except Exception:
                # Fallback if AI call fails
                pass

        # Fallback implementation
        return f"You examine the {item_name}. [Detailed item descriptions coming soon]"

    async def list_inventory(self, current_inventory: List[str]) -> str:
        """Get a formatted list of inventory items."""
        if not current_inventory:
            return "Your inventory is empty."

        return f"You are carrying: {', '.join(current_inventory)}"
