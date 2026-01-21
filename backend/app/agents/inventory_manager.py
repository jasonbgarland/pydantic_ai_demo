"""Inventory Manager Agent - Specialist for item interactions and inventory management."""
import os
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from pydantic import BaseModel, Field

try:
    from pydantic_ai import Agent, RunContext
    from pydantic_ai.models.openai import OpenAIModel
    PYDANTIC_AI_AVAILABLE = True
except ImportError:
    # Fallback for testing or when PydanticAI is not available
    PYDANTIC_AI_AVAILABLE = False
    Agent = None
    RunContext = None

from ..tools.rag_tools import find_items_in_location
from ..utils.name_utils import normalize_item_name, display_item_name

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

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
    async def check_item_availability(
            ctx: RunContext[InventoryContext], item_name: str, location: str) -> bool:
        """Check if an item is available in the current location."""
        room_items = ctx.deps.room_items.get(location, [])
        return item_name in room_items


    async def validate_inventory_space(ctx: RunContext[InventoryContext]) -> bool:
        """Check if there's space in the inventory for another item."""
        return len(ctx.deps.current_inventory) < ctx.deps.inventory_limit


    async def get_item_properties(
            ctx: RunContext[InventoryContext],
            item_name: str) -> Dict[str, Any]:  # pylint: disable=unused-argument
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
        tools=[check_item_availability, validate_inventory_space, get_item_properties],  # pylint: disable=possibly-used-before-assignment
    )
else:
    INVENTORY_AGENT = None


class InventoryManager:
    """Wrapper class for the inventory management agent.

    Provides compatibility with existing code while using PydanticAI underneath.
    """

    def __init__(self):
        """Initialize the InventoryManager."""
        self.context = InventoryContext()

    async def pickup_item(
            self, item_name: str, current_inventory: List[str],
            current_location: str = None) -> Dict[str, Any]:
        """Handle picking up an item."""
        logger.info(
            "PICKUP REQUEST: item=%s, location=%s, inventory=%s",
            item_name, current_location, current_inventory
        )
        self.context.current_inventory = current_inventory.copy()

        # Check for compound names first (before any processing)
        if " and " in item_name or "," in item_name:
            return {
                "success": False,
                "message": "You can only pick up one item at a time. Please specify a single item.",
                "inventory_update": current_inventory
            }

        # Normalize item name for matching using shared utility
        normalized_input = normalize_item_name(item_name)

        # Item aliases - map common short names to possible full names
        # When user says "potion", check for both "potion" and "healing_potion"
        item_aliases = {
            'potion': ['potion', 'healing_potion'],
            'health_potion': ['healing_potion'],
            'rope': ['rope', 'magical_rope'],
            'gear': ['gear', 'climbing_gear'],
            'journal': ['journal', 'explorer_journal'],
            'crystal': ['crystal', 'crystal_of_echoing_depths'],
            'pack': ['pack', 'leather_pack'],
            'backpack': ['backpack', 'leather_pack'],
        }

        # Build list of names to check (normalized_input + any aliases)
        names_to_check = [normalized_input]
        if normalized_input in item_aliases:
            names_to_check.extend(item_aliases[normalized_input])

        # Populate room_items from structured data so the AI agent can validate
        if current_location:
            available_items = find_items_in_location(current_location)
            logger.info("AVAILABLE ITEMS: %s", available_items)

            # Check if any of the candidate names exist in available items
            item_match = None
            for candidate_name in names_to_check:
                for available_item in available_items:
                    if candidate_name == normalize_item_name(available_item):
                        item_match = available_item  # Use the canonical name from the room data
                        break
                if item_match:
                    break

            if not item_match:
                logger.info(
                    "ITEM NOT FOUND: %s (normalized: %s) not in %s",
                    item_name, normalized_input, available_items
                )
                return {
                    "success": False,
                    "message": f"You don't see any {item_name} here.",
                    "inventory_update": current_inventory
                }

            # Use the matched canonical name for the rest of the process
            item_name = item_match

            self.context.room_items = {current_location: available_items}

        if PYDANTIC_AI_AVAILABLE and INVENTORY_AGENT:
            try:
                logger.info(
                    "CALLING AI AGENT with context: room_items=%s",
                    self.context.room_items
                )
                result = await INVENTORY_AGENT.run(
                    f"Player wants to pick up: {item_name} from "
                    f"{current_location}. Check if the item exists in "
                    f"the location before allowing pickup.",
                    deps=self.context
                )
                logger.info(
                    "AI AGENT RESULT: success=%s, message=%s",
                    result.data.success, result.data.message
                )
                return {
                    "success": result.data.success,
                    "message": result.data.message,
                    "inventory_update": result.data.inventory_update
                }
            except Exception as e:
                # Fallback if AI call fails
                logger.error("AI AGENT FAILED: %s", e, exc_info=True)

        # Fallback implementation - validate manually if AI not available
        logger.info("USING FALLBACK VALIDATION")

        # Check if item is already in inventory (use matched canonical name)
        check_name = item_match if item_match else item_name
        if check_name in current_inventory:
            return {
                "success": False,
                "message": f"You already have the {display_item_name(check_name)}.",
                "inventory_update": current_inventory
            }

        new_inventory = current_inventory + [check_name]
        return {
            "success": True,
            "message": f"You pick up the {display_item_name(check_name)}.",
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

        # Normalize the item name to handle variations and extra text
        normalized_input = normalize_item_name(item_name)
        
        # Find the actual item in inventory that matches
        matched_item = None
        for inv_item in current_inventory:
            if normalize_item_name(inv_item) == normalized_input:
                matched_item = inv_item
                break
            # Also check if the normalized input contains the item name
            # This handles "use grappling hook to cross" -> finds "grappling_hook"
            if normalize_item_name(inv_item) in normalized_input:
                matched_item = inv_item
                break
        
        # If we didn't find a match, return error immediately
        if not matched_item:
            return {
                "success": False,
                "message": f"You don't have a {item_name} to use.",
                "inventory_update": current_inventory
            }

        if PYDANTIC_AI_AVAILABLE and INVENTORY_AGENT:
            try:
                # Use the matched item name for the AI agent
                result = await INVENTORY_AGENT.run(
                    f"Player wants to use: {matched_item}",
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
        return {
            "success": True,
            "message": f"You use the {display_item_name(matched_item)}. [Item effects not yet implemented]",
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

    async def get_inventory_summary(self, current_inventory: List[str]) -> str:
        """Get a summary of the player's inventory.

        This is an alias for list_inventory to maintain compatibility.
        """
        return await self.list_inventory(current_inventory)
