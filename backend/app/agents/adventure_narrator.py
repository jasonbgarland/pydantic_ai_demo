"""Adventure Narrator Agent - Main game command orchestrator."""
import asyncio
from enum import Enum
from typing import Dict, Optional, List, Any
from pydantic import BaseModel, Field


class CommandType(str, Enum):
    """Types of commands the adventure narrator can handle."""
    MOVEMENT = "movement"
    EXAMINE = "examine"
    PICKUP = "pickup"
    DROP = "drop"
    USE = "use"
    TALK = "talk"
    ATTACK = "attack"
    LOOK = "look"
    INVENTORY = "inventory"
    UNKNOWN = "unknown"


class ParsedCommand(BaseModel):
    """Structured representation of a player command after parsing."""
    command_type: CommandType
    action: str = Field(description="The main action verb")
    target: Optional[str] = Field(default=None, description="Object being acted upon")
    direction: Optional[str] = Field(default=None, description="Movement direction")
    parameters: Dict = Field(default_factory=dict, description="Additional command parameters")
    confidence: float = Field(default=1.0, description="Parser confidence (0-1)")


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
    Main orchestrator agent that parses player commands and delegates to specialist agents.

    Responsibilities:
    - Parse natural language commands into structured intents
    - Determine which specialist agents to involve
    - Orchestrate responses from multiple agents
    - Compose final narrative response
    """

    def __init__(self, room_descriptor=None, inventory_manager=None, entity_manager=None):
        """Initialize the AdventureNarrator with specialist agents."""
        # Specialist agents for delegation
        self.room_descriptor = room_descriptor
        self.inventory_manager = inventory_manager
        self.entity_manager = entity_manager

        # Movement direction mappings
        self.movement_keywords = {
            "north", "n", "up", "upward", "forward",
            "south", "s", "down", "downward", "back", "backward",
            "east", "e", "right",
            "west", "w", "left",
            "northeast", "ne", "northwest", "nw",
            "southeast", "se", "southwest", "sw"
        }

        # Action verb mappings
        self.action_verbs = {
            # Movement
            "go": CommandType.MOVEMENT,
            "move": CommandType.MOVEMENT,
            "walk": CommandType.MOVEMENT,
            "run": CommandType.MOVEMENT,
            "travel": CommandType.MOVEMENT,
            "head": CommandType.MOVEMENT,
            # Examination
            "examine": CommandType.EXAMINE,
            "inspect": CommandType.EXAMINE,
            "check": CommandType.EXAMINE,
            "view": CommandType.EXAMINE,
            "see": CommandType.EXAMINE,
            # Item interaction
            "get": CommandType.PICKUP,
            "take": CommandType.PICKUP,
            "pickup": CommandType.PICKUP,
            "grab": CommandType.PICKUP,
            "collect": CommandType.PICKUP,
            "drop": CommandType.DROP,
            "put": CommandType.DROP,
            "place": CommandType.DROP,
            "leave": CommandType.DROP,
            "use": CommandType.USE,
            "utilize": CommandType.USE,
            "activate": CommandType.USE,
            "apply": CommandType.USE,
            # Entity interaction
            "talk": CommandType.TALK,
            "speak": CommandType.TALK,
            "chat": CommandType.TALK,
            "converse": CommandType.TALK,
            "attack": CommandType.ATTACK,
            "fight": CommandType.ATTACK,
            "hit": CommandType.ATTACK,
            "strike": CommandType.ATTACK,
            "kill": CommandType.ATTACK,
            # Meta commands
            "inventory": CommandType.INVENTORY,
            "items": CommandType.INVENTORY,
            "bag": CommandType.INVENTORY,
            "backpack": CommandType.INVENTORY
        }

    def parse_command(self, raw_command: str, parameters: Optional[Dict] = None) -> ParsedCommand:
        """
        Parse a raw text command into structured intent.

        Args:
            raw_command: Natural language command from player
            parameters: Optional additional parameters from the GameCommand

        Returns:
            ParsedCommand with structured intent and confidence level
        """
        if not raw_command or not raw_command.strip():
            return ParsedCommand(
                command_type=CommandType.UNKNOWN,
                action="",
                confidence=0.0
            )

        # Normalize command
        words = raw_command.lower().strip().split()
        if not words:
            return ParsedCommand(
                command_type=CommandType.UNKNOWN,
                action=raw_command,
                confidence=0.0
            )

        # Handle single word commands
        if len(words) == 1:
            return self._parse_single_word(words[0], parameters or {})

        # Handle multi-word commands
        return self._parse_multi_word(words, parameters or {})

    def _parse_single_word(self, word: str, parameters: Dict) -> ParsedCommand:
        """Parse single-word commands."""
        # Check if it's a direction (implicit movement)
        if word in self.movement_keywords:
            return ParsedCommand(
                command_type=CommandType.MOVEMENT,
                action="go",
                direction=word,
                parameters=parameters,
                confidence=0.9
            )

        # Check if it's an action verb
        if word in self.action_verbs:
            cmd_type = self.action_verbs[word]
            return ParsedCommand(
                command_type=cmd_type,
                action=word,
                parameters=parameters,
                confidence=0.8
            )

        # Special case for "look" without target
        if word == "look":
            return ParsedCommand(
                command_type=CommandType.LOOK,
                action="look",
                target="around",
                parameters=parameters,
                confidence=0.9
            )

        return ParsedCommand(
            command_type=CommandType.UNKNOWN,
            action=word,
            confidence=0.3
        )

    def _parse_multi_word(self, words: List[str], parameters: Dict) -> ParsedCommand:
        """Parse multi-word commands."""
        first_word = words[0]

        # Handle "look at <target>" before general action mapping
        if first_word == "look" and len(words) >= 2:
            if words[1] == "at" and len(words) >= 3:
                target = " ".join(words[2:])
            else:
                target = " ".join(words[1:])
            return ParsedCommand(
                command_type=CommandType.EXAMINE,
                action="examine",
                target=target,
                parameters=parameters,
                confidence=0.9
            )

        # Handle "go <direction>" or "<action> <direction>"
        if first_word in ["go", "move", "walk", "head"] and len(words) >= 2:
            direction = words[1]
            if direction in self.movement_keywords:
                return ParsedCommand(
                    command_type=CommandType.MOVEMENT,
                    action=first_word,
                    direction=direction,
                    parameters=parameters,
                    confidence=0.95
                )

        # Handle "<action> <target>" patterns
        if first_word in self.action_verbs and len(words) >= 2:
            cmd_type = self.action_verbs[first_word]
            target = " ".join(words[1:])  # Join remaining words as target
            return ParsedCommand(
                command_type=cmd_type,
                action=first_word,
                target=target,
                parameters=parameters,
                confidence=0.85
            )

        # Fallback: treat as unknown command
        return ParsedCommand(
            command_type=CommandType.UNKNOWN,
            action=" ".join(words),
            confidence=0.2
        )

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
                    current_location, direction
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
                else:
                    return GameResponse(
                        agent="RoomDescriptor",
                        narrative=f"You cannot go {direction} from here.",
                        success=False,
                        metadata={'direction': direction, 'blocked': True}
                    )
            except Exception as e:
                # Fallback if agent call fails
                narrative = (
                    f"You head {direction} from {current_location}. "
                    f"[Agent error: {str(e)}]"
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

        if self.room_descriptor:
            try:
                if target == 'around':
                    description = await self.room_descriptor.get_room_description(current_location)
                else:
                    description = await self.room_descriptor.examine_environment(
                        current_location, target
                    )
                return GameResponse(
                    agent="RoomDescriptor",
                    narrative=description,
                    metadata={'examined': target, 'location': current_location}
                )
            except Exception as e:
                narrative = f"You examine {target}. [Agent error: {str(e)}]"
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

        if self.inventory_manager:
            try:
                if action in ['get', 'take', 'pickup', 'grab', 'collect']:
                    result = await self.inventory_manager.pickup_item(target, current_inventory)
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
            except Exception as e:
                narrative = f"You {action} the {target}. [Agent error: {str(e)}]"
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
        self, command: ParsedCommand, game_state: Dict[str, Any]
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
            except Exception as e:
                narrative = f"You {action} {target}. [Agent error: {str(e)}]"
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
            except Exception as e:
                narrative = f"Inventory check failed. [Agent error: {str(e)}]"
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
