"""Adventure Narrator Agent - Main game command orchestrator."""
import asyncio
from typing import Dict, Optional, List, Any
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

    def __init__(self, room_descriptor=None, inventory_manager=None, entity_manager=None):
        """Initialize the AdventureNarrator with specialist agents."""
        # AI-powered intent classification
        self.intent_parser = IntentParser()
        
        # Specialist agents for delegation
        self.room_descriptor = room_descriptor
        self.inventory_manager = inventory_manager
        self.entity_manager = entity_manager

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
        if parsed_command.command_type == CommandType.MOVEMENT:
            return await self._handle_movement(parsed_command, game_state)
        if parsed_command.command_type in [CommandType.EXAMINE, CommandType.LOOK]:
            return await self._handle_examination(parsed_command, game_state)
        if parsed_command.command_type in [CommandType.PICKUP, CommandType.DROP, CommandType.USE]:
            return await self._handle_item_interaction(parsed_command, game_state)
        if parsed_command.command_type in [CommandType.TALK, CommandType.ATTACK]:
            return await self._handle_entity_interaction(parsed_command, game_state)
        if parsed_command.command_type == CommandType.INVENTORY:
            return await self._handle_inventory(parsed_command, game_state)
        if parsed_command.command_type == CommandType.ABILITY:
            return await self._handle_ability(parsed_command, game_state)
        # Unknown command
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

        if self.room_descriptor:
            try:
                movement_result = await self.room_descriptor.handle_movement(
                    current_location, direction, game_state=game_state
                )
                if movement_result['success']:
                    narrative = movement_result['description']
                    new_location = movement_result['new_location']
                    return GameResponse(
                        agent="RoomDescriptor",
                        narrative=narrative,
                        game_state_updates={'location': new_location},
                        metadata={'direction': direction, 'from_location': current_location}
                    )
                return GameResponse(
                    agent="RoomDescriptor",
                    narrative=f"You cannot go {direction} from here.",
                    success=False,
                    metadata={'direction': direction, 'blocked': True}
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
                if action in ['get', 'take', 'pickup', 'grab', 'collect']:
                    result = await self.inventory_manager.pickup_item(target, current_inventory, current_location)
                elif action in ['drop', 'put', 'place', 'leave']:
                    result = await self.inventory_manager.drop_item(target, current_inventory)
                elif action in ['use', 'utilize', 'activate', 'apply']:
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

    async def _handle_entity_interaction(
        self, command: ParsedCommand, game_state: Dict[str, Any]  # pylint: disable=unused-argument
    ) -> GameResponse:
        """Handle entity interactions by delegating to EntityManager."""
        target = command.target or 'someone'
        action = command.action

        if self.entity_manager:
            try:
                if action in ['talk', 'speak', 'chat', 'converse']:
                    result = await self.entity_manager.talk_to_entity(target)
                elif action in ['attack', 'fight', 'hit', 'strike', 'kill']:
                    result = await self.entity_manager.attack_entity(target)
                else:
                    result = {
                        'success': False,
                        'message': f"Unknown entity action: {action}",
                        'state_changes': {}
                    }

                game_state_updates = result.get('state_changes', {})
                return GameResponse(
                    agent="EntityManager",
                    narrative=result['message'],
                    success=result['success'],
                    game_state_updates=game_state_updates,
                    metadata={'entity_action': action, 'target': target}
                )
            except Exception as exc:
                narrative = f"You {action} {target}. [Agent error: {str(exc)}]"
        else:
            # Fallback when no agent available
            narrative = (
                f"You {action} {target}. "
                "[Entity interaction logic not yet implemented]"
            )

        return GameResponse(
            agent="AdventureNarrator",
            narrative=narrative,
            metadata={'entity_action': action, 'target': target}
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

        return GameResponse(
            agent="SimpleAbilitySystem",
            narrative=ability_result["narrative"],
            game_state_updates=ability_result.get("effects", {}),
            success=ability_result["success"],
            metadata={"ability_name": actual_ability}
        )

    async def call_agents(self, agent_name: str, method_name: str, *args, **kwargs):
        """Async tool for calling specialist agents by name."""
        agent_map = {
            'room_descriptor': self.room_descriptor,
            'inventory_manager': self.inventory_manager,
            'entity_manager': self.entity_manager
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
