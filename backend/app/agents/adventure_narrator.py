"""Adventure Narrator Agent - Main game command orchestrator."""
import asyncio
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field

from app.mechanics import SimpleAbilitySystem
from app.agents.command_models import CommandType, ParsedCommand
from app.agents.intent_parser import IntentParser


class GameResponse(BaseModel):
    """Structured response from the adventure narrator."""
    agent: str = Field(description="Which agent generated the response")
    narrative: str = Field(description="The narrative text for the player")
    game_state_updates: Dict[str, Any] = Field(
        default_factory=dict, description="Updates to apply to game state"
    )
    success: bool = Field(default=True, description="Whether the action was successful")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional response metadata"
    )


class AdventureNarrator:
    """
    Main orchestrator agent that coordinates specialist agents.

    Demonstrates the Orchestration Pattern:
    - Uses IntentParser (AI classification) to understand commands
    - Determines which specialist agents to involve
    - Orchestrates responses from multiple agents
    - Composes final narrative response
    """

    def __init__(self, room_descriptor=None, inventory_manager=None):
        """Initialize the AdventureNarrator with specialist agents."""
        # AI-powered intent classification
        self.intent_parser = IntentParser()

        # Specialist agents for delegation
        self.room_descriptor = room_descriptor
        self.inventory_manager = inventory_manager

    async def parse_command(self, raw_command: str, parameters: Optional[Dict] = None) -> ParsedCommand:
        """
        Parse a raw text command into structured intent using AI.

        Args:
            raw_command: Natural language command from player
            parameters: Optional additional parameters (currently unused)

        Returns:
            ParsedCommand with AI-classified intent
        """
        return await self.intent_parser.parse_command(raw_command)

    async def handle_command(
        self, parsed_command: ParsedCommand, game_state: Dict[str, Any]
    ) -> GameResponse:
        """Orchestrate response to a parsed command by delegating to specialist agents."""

        # Check for exit/escape commands first (before checking command_type)
        # These work from cave_entrance with the crystal
        current_location = game_state.get('location', 'unknown')
        if parsed_command.action in ['leave', 'escape', 'exit', 'flee'] or (parsed_command.target and 'cave' in parsed_command.target.lower()):
            if current_location == 'cave_entrance':
                inventory = game_state.get('inventory', [])
                has_crystal = any('crystal' in str(item).lower() for item in inventory)

                if has_crystal:
                    # Victory!
                    from app.mechanics import get_victory_narrative, GameStatus
                    victory_narrative = get_victory_narrative()
                    game_state_updates = {
                        'location': 'outside',
                        'game_status': GameStatus.VICTORY
                    }

                    return GameResponse(
                        agent="AdventureNarrator",
                        narrative=victory_narrative,
                        game_state_updates=game_state_updates,
                        metadata={'action': 'victory', 'escaped': True}
                    )

                narrative = (
                    "You stand at the cave entrance, daylight beckoning. But you came here for the legendary "
                    "Crystal of Echoing Depths. You won't leave empty-handed - not after coming this far."
                )
                return GameResponse(
                    agent="AdventureNarrator",
                    narrative=narrative,
                    success=False,
                    metadata={'action': 'attempted_escape', 'missing_crystal': True}
                )

        # Route to specialist handlers based on command type
        if parsed_command.command_type == CommandType.MOVEMENT:
            return await self._handle_movement(parsed_command, game_state)
        if parsed_command.command_type in [CommandType.EXAMINE, CommandType.LOOK]:
            return await self._handle_examination(parsed_command, game_state)
        if parsed_command.command_type in [CommandType.PICKUP, CommandType.DROP, CommandType.USE]:
            return await self._handle_item_interaction(parsed_command, game_state)
        if parsed_command.command_type == CommandType.INVENTORY:
            return await self._handle_inventory(parsed_command, game_state)
        if parsed_command.command_type == CommandType.ABILITY:
            return await self._handle_ability(parsed_command, game_state)

        # Unknown command
        if parsed_command.command_type == CommandType.UNKNOWN:
            return GameResponse(
                agent="AdventureNarrator",
                narrative=(
                    f"I don't understand '{parsed_command.action}'. "
                    "Try commands like 'go north', 'examine door', or 'take key'."
                ),
                success=False
            )

        # Fallback for any other case
        return GameResponse(
            agent="AdventureNarrator",
            narrative=(
                f"I don't understand '{parsed_command.action}'. "
                "Try commands like 'go north', 'examine door', or 'take key'."
            ),
            success=False
        )

    async def _handle_movement(
        self, command: ParsedCommand, game_state: Dict[str, Any]
    ) -> GameResponse:
        """Handle movement commands by delegating to RoomDescriptor."""
        current_location = game_state.get('location', 'unknown')
        direction = command.direction or 'somewhere'

        # Handle contextual "cross" commands
        # "cross chasm", "cross safely", "cross bridge" at specific locations
        if command.action in ['cross', 'traverse'] or direction in ['chasm', 'bridge', 'safely']:
            if current_location == 'cave_entrance':
                direction = 'east'  # To yawning_chasm
            elif current_location == 'yawning_chasm':
                # Handle crossing the chasm - toggles which side you're on
                inventory = game_state.get('inventory', [])
                crossing_items = ['magical_rope', 'grappling_hook', 'climbing_gear']
                has_equipment = any(item in inventory for item in crossing_items)

                # Check for ability flag (Rogue dash)
                temp_flags = game_state.get('temp_flags', {})
                ability_used = temp_flags.get('ability_used_for_crossing', False)

                if has_equipment or ability_used:
                    # Toggle which side of the chasm you're on
                    current_side = temp_flags.get('chasm_east_side', False)
                    new_side = not current_side

                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info("CROSS CHASM: current_side=%s, new_side=%s, current temp_flags=%s",
                                current_side, new_side, temp_flags)

                    game_state_updates = {
                        'temp_flags': {
                            'chasm_east_side': new_side,
                            'ability_used_for_crossing': False  # Clear the ability flag
                        }
                    }

                    logger.info("CROSS CHASM: game_state_updates=%s", game_state_updates)

                    # Determine which item was used and direction
                    if has_equipment:
                        item_used = next((item for item in crossing_items if item in inventory), None)
                        item_name = item_used.replace('_', ' ') if item_used else 'equipment'
                        cross_narrative = f"You carefully secure the {item_name} and make your way across the treacherous chasm. The ancient stone holds beneath your weight."
                    else:
                        cross_narrative = "With a powerful burst of speed, you dash across the chasm in a single leap!"

                    if new_side:
                        narrative = f"{cross_narrative} You're now on the eastern side - the path to the Crystal Treasury lies ahead."
                    else:
                        narrative = f"{cross_narrative} You're now on the western side - the path back to the cave entrance is clear."

                    return GameResponse(
                        agent="AdventureNarrator",
                        narrative=narrative,
                        game_state_updates=game_state_updates,
                        success=True,
                        metadata={'action': 'cross_chasm', 'east_side': new_side}
                    )

                narrative = "The chasm yawns before you - far too wide to jump. You'll need rope, climbing gear, or a grappling hook to cross safely."
                return GameResponse(
                    agent="AdventureNarrator",
                    narrative=narrative,
                    success=False,
                    metadata={'action': 'cross_chasm'}
                )
            elif current_location == 'crystal_treasury':
                direction = 'west'  # Back across chasm

        if self.room_descriptor:
            try:
                movement_result = await self.room_descriptor.handle_movement(
                    current_location, direction, game_state=game_state
                )
                if movement_result['success']:
                    narrative = movement_result['description']
                    new_location = movement_result['new_location']

                    # Merge location update with any state updates from movement (like clearing flags)
                    game_state_updates = {'location': new_location}
                    if 'state_updates' in movement_result:
                        game_state_updates.update(movement_result['state_updates'])

                    return GameResponse(
                        agent="RoomDescriptor",
                        narrative=narrative,
                        game_state_updates=game_state_updates,
                        metadata={'direction': direction, 'from_location': current_location}
                    )
                # Movement blocked - use the description from the result
                return GameResponse(
                    agent="RoomDescriptor",
                    narrative=movement_result.get('description', f"You cannot go {direction} from here."),
                    success=False,
                    metadata={'direction': direction, 'blocked': True, 'reason': movement_result.get('blocked_reason')}
                )
            except Exception as exc:
                # Fallback if agent call fails
                narrative = (
                    f"You head {direction} from {current_location}. "
                    f"[Agent error: {str(exc)}]"
                )
        else:
            # Fallback when no agent available
            narrative = (
                f"You head {direction} from {current_location}. "
                "[Movement logic not yet implemented]"
            )

        return GameResponse(
            agent="AdventureNarrator",
            narrative=narrative,
            game_state_updates={'location': f"{current_location}_{direction}"},
            metadata={'direction': direction, 'from_location': current_location}
        )

    async def _handle_examination(
        self, command: ParsedCommand, game_state: Dict[str, Any]
    ) -> GameResponse:
        """Handle examination commands by delegating to RoomDescriptor."""
        target = command.target or 'around'
        current_location = game_state.get('location', 'unknown')
        current_inventory = game_state.get('inventory', [])

        if self.room_descriptor:
            try:
                if target == 'around':
                    description = await self.room_descriptor.get_room_description(
                        current_location, game_state=game_state
                    )
                else:
                    character_class = game_state.get('character_class', '') if game_state else ''
                    description = await self.room_descriptor.examine_environment(
                        current_location, target, inventory=current_inventory,
                        character_class=character_class
                    )
                return GameResponse(
                    agent="RoomDescriptor",
                    narrative=description,
                    metadata={'examined': target, 'location': current_location}
                )
            except Exception as exc:
                narrative = f"You examine {target}. [Agent error: {str(exc)}]"
        else:
            # Fallback when no agent available
            if target == 'around':
                narrative = (
                    "You look around. You are in an unknown place. "
                    "[Room description logic not yet implemented]"
                )
            else:
                narrative = f"You examine the {target}. [Examination logic not yet implemented]"

        return GameResponse(
            agent="AdventureNarrator",
            narrative=narrative,
            metadata={'examined': target}
        )

    async def _handle_item_interaction(
        self, command: ParsedCommand, game_state: Dict[str, Any]
    ) -> GameResponse:
        """Handle item interactions by delegating to InventoryManager."""
        target = command.target or 'something'
        action = command.action
        current_inventory = game_state.get('inventory', [])
        current_location = game_state.get('location', '')

        if self.inventory_manager:
            try:
                # Special handling for taking the crystal - triggers trap and collapse
                if command.command_type == CommandType.PICKUP and target and 'crystal' in target.lower():
                    if current_location != 'crystal_treasury':
                        # Not in the treasury, handle normally
                        result = await self.inventory_manager.pickup_item(
                            target,
                            current_inventory,
                            current_location
                        )
                        return GameResponse(
                            agent="InventoryManager",
                            narrative=result['narrative'],
                            game_state_updates={'inventory': result['inventory_update']},
                            success=result['success']
                        )

                    temp_flags = game_state.get('temp_flags', {})
                    collapse_triggered = game_state.get('collapse_triggered', False)
                    has_crystal = any('crystal' in str(item).lower() for item in current_inventory)

                    if has_crystal:
                        narrative = "You already possess the Crystal of Echoing Depths. Its weight reminds you of the urgency to escape."
                        return GameResponse(
                            agent="AdventureNarrator",
                            narrative=narrative,
                            success=False,
                            metadata={'action': 'already_have_crystal'}
                        )

                    # First time taking the crystal - triggers the trap!
                    if collapse_triggered:
                        # Already collapsed, just try to pick up (shouldn't happen)
                        result = await self.inventory_manager.pickup_item(
                            'Crystal of Echoing Depths',
                            current_inventory,
                            current_location
                        )
                        return GameResponse(
                            agent="InventoryManager",
                            narrative=result['narrative'],
                            game_state_updates={'inventory': result['inventory_update']},
                            success=result['success']
                        )

                    # Add crystal to inventory
                    result = await self.inventory_manager.pickup_item(
                        'Crystal of Echoing Depths',
                        current_inventory,
                        current_location
                    )

                    # Trigger the collapse
                    game_state_updates = {
                        'inventory': result['inventory_update'],
                        'collapse_triggered': True,
                        'turns_since_collapse': 0
                    }

                    narrative = (
                        "You reach out and carefully lift the Crystal of Echoing Depths from its pedestal. "
                        "The moment it breaks contact, the crystal pulses with brilliant blue light.\n\n"
                        "**CRACK!**\n\n"
                        "The pressure plate beneath the pedestal sinks with a grinding sound of ancient stone. "
                        "Mechanisms hidden in the walls engage with metallic screeches. Dust begins to rain from "
                        "the ceiling as the first tremor shakes the chamber. The murals seem to scream their "
                        "warnings - the cave is collapsing!\n\n"
                        "You clutch the crystal tightly. **You must escape before you're buried alive!**"
                    )

                    return GameResponse(
                        agent="AdventureNarrator",
                        narrative=narrative,
                        game_state_updates=game_state_updates,
                        success=True,
                        metadata={'action': 'take_crystal_trigger_collapse'}
                    )

                # Trust the AI's command classification - no need to check action verbs
                if command.command_type == CommandType.PICKUP:
                    result = await self.inventory_manager.pickup_item(target, current_inventory, current_location)
                elif command.command_type == CommandType.DROP:
                    result = await self.inventory_manager.drop_item(target, current_inventory)
                elif command.command_type == CommandType.USE:
                    result = await self.inventory_manager.use_item(target, current_inventory)
                else:
                    result = {
                        'success': False,
                        'message': f"Unknown item action: {action}",
                        'inventory_update': current_inventory
                    }

                game_state_updates = {}
                if 'inventory_update' in result:
                    game_state_updates['inventory'] = result['inventory_update']
                if 'state_changes' in result:
                    game_state_updates.update(result['state_changes'])

                return GameResponse(
                    agent="InventoryManager",
                    narrative=result['message'],
                    success=result['success'],
                    game_state_updates=game_state_updates,
                    metadata={'item_action': action, 'target': target}
                )
            except Exception as exc:
                narrative = f"You {action} the {target}. [Agent error: {str(exc)}]"
        else:
            # Fallback when no agent available
            narrative = (
                f"You {action} the {target}. "
                "[Item interaction logic not yet implemented]"
            )

        return GameResponse(
            agent="AdventureNarrator",
            narrative=narrative,
            metadata={'item_action': action, 'target': target}
        )

    async def _handle_inventory(
        self, _: ParsedCommand, game_state: Dict[str, Any]
    ) -> GameResponse:
        """Handle inventory commands by delegating to InventoryManager."""
        inventory = game_state.get('inventory', [])

        if self.inventory_manager:
            try:
                narrative = await self.inventory_manager.get_inventory_summary(inventory)
                return GameResponse(
                    agent="InventoryManager",
                    narrative=narrative,
                    metadata={'inventory': inventory}
                )
            except Exception as exc:
                narrative = f"Inventory check failed. [Agent error: {str(exc)}]"
        else:
            # Fallback when no agent available
            if not inventory:
                narrative = "Your inventory is empty."
            else:
                items_list = ", ".join(inventory)
                narrative = f"You are carrying: {items_list}"

        return GameResponse(
            agent="AdventureNarrator",
            narrative=narrative,
            metadata={'inventory': inventory}
        )

    async def _handle_ability(
        self, command: ParsedCommand, game_state: Dict[str, Any]
    ) -> GameResponse:
        """Handle ability usage by delegating to the SimpleAbilitySystem."""
        ability_name = command.parameters.get("ability_name", "")
        character = game_state.get("character", {})
        character_class = character.get("character_class", "Warrior")
        current_location = game_state.get('location', '')

        # Parse ability command to check if valid
        parse_result = SimpleAbilitySystem.parse_ability_command(ability_name, character_class)

        if not parse_result["is_ability"]:
            return GameResponse(
                agent="SimpleAbilitySystem",
                narrative=f"'{ability_name}' is not a recognized ability for {character_class}s.",
                success=False,
                metadata={"ability_name": ability_name, "character_class": character_class}
            )

        actual_ability = parse_result["ability_name"]

        # Use the ability
        ability_result = SimpleAbilitySystem.use_ability(
            actual_ability,
            character_class,
            game_state
        )

        # Set flag if dash used at chasm (allows crossing without equipment)
        game_state_updates = ability_result.get("effects", {})
        if actual_ability == "dash" and current_location == "yawning_chasm":
            if 'temp_flags' not in game_state_updates:
                game_state_updates['temp_flags'] = {}
            game_state_updates['temp_flags']['ability_used_for_crossing'] = True
            # Enhance narrative for context
            ability_result["narrative"] += " You're ready to leap across the chasm!"

        return GameResponse(
            agent="SimpleAbilitySystem",
            narrative=ability_result["narrative"],
            game_state_updates=game_state_updates,
            success=ability_result["success"],
            metadata={"ability_name": actual_ability}
        )

    async def call_agents(self, agent_name: str, method_name: str, *args, **kwargs):
        """Async tool for calling specialist agents by name."""
        agent_map = {
            'room_descriptor': self.room_descriptor,
            'inventory_manager': self.inventory_manager
        }

        agent = agent_map.get(agent_name)
        if not agent:
            raise ValueError(f"Unknown agent: {agent_name}")

        method = getattr(agent, method_name, None)
        if not method:
            raise ValueError(f"Agent {agent_name} has no method {method_name}")

        # Handle both sync and async methods
        if asyncio.iscoroutinefunction(method):
            return await method(*args, **kwargs)
        return method(*args, **kwargs)
