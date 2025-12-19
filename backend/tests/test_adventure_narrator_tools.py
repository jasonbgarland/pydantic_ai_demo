"""Unit tests for AdventureNarrator tools and integration with specialist agents."""
import unittest
from unittest.mock import AsyncMock, MagicMock
from app.agents.adventure_narrator import AdventureNarrator, CommandType, ParsedCommand
from app.agents.room_descriptor import RoomDescriptor
from app.agents.inventory_manager import InventoryManager
from app.agents.entity_manager import EntityManager


class TestAdventureNarratorTools(unittest.IsolatedAsyncioTestCase):
    """Test AdventureNarrator tools and agent integration."""

    def setUp(self):
        """Set up test fixtures with mock agents."""
        self.mock_room_descriptor = MagicMock(spec=RoomDescriptor)
        self.mock_inventory_manager = MagicMock(spec=InventoryManager)
        self.mock_entity_manager = MagicMock(spec=EntityManager)

        self.narrator = AdventureNarrator(
            room_descriptor=self.mock_room_descriptor,
            inventory_manager=self.mock_inventory_manager,
            entity_manager=self.mock_entity_manager
        )

        self.sample_game_state = {
            "location": "dungeon_entrance",
            "inventory": ["rusty_key", "torch"],
            "discovered": ["dungeon_entrance"],
            "turn_count": 5
        }

    async def test_call_agents_tool_room_descriptor(self):
        """Test call_agents tool with room_descriptor."""
        # Setup mock return value
        self.mock_room_descriptor.get_room_description.return_value = "A dark room"

        # Call agent through tool
        result = await self.narrator.call_agents('room_descriptor', 'get_room_description', 'test_room')

        # Verify
        self.assertEqual(result, "A dark room")
        self.mock_room_descriptor.get_room_description.assert_called_once_with('test_room')

    async def test_call_agents_tool_inventory_manager(self):
        """Test call_agents tool with inventory_manager."""
        # Setup mock return value
        expected_result = {'success': True, 'message': 'Item picked up'}
        self.mock_inventory_manager.pickup_item.return_value = expected_result

        # Call agent through tool
        result = await self.narrator.call_agents('inventory_manager', 'pickup_item', 'sword', [])

        # Verify
        self.assertEqual(result, expected_result)
        self.mock_inventory_manager.pickup_item.assert_called_once_with('sword', [])

    async def test_call_agents_tool_entity_manager(self):
        """Test call_agents tool with entity_manager."""
        # Setup mock return value
        expected_result = {'success': True, 'message': 'You talk to the wizard'}
        self.mock_entity_manager.talk_to_entity.return_value = expected_result

        # Call agent through tool
        result = await self.narrator.call_agents('entity_manager', 'talk_to_entity', 'wizard')

        # Verify
        self.assertEqual(result, expected_result)
        self.mock_entity_manager.talk_to_entity.assert_called_once_with('wizard')

    async def test_call_agents_tool_unknown_agent(self):
        """Test call_agents tool with unknown agent."""
        with self.assertRaises(ValueError) as context:
            await self.narrator.call_agents('unknown_agent', 'some_method')

        self.assertIn("Unknown agent: unknown_agent", str(context.exception))

    async def test_call_agents_tool_unknown_method(self):
        """Test call_agents tool with unknown method."""
        with self.assertRaises(ValueError) as context:
            await self.narrator.call_agents('room_descriptor', 'nonexistent_method')

        self.assertIn("has no method nonexistent_method", str(context.exception))

    async def test_movement_with_room_descriptor_agent(self):
        """Test movement command integration with room_descriptor agent."""
        # Setup mock
        self.mock_room_descriptor.handle_movement = AsyncMock(return_value={
            'success': True,
            'description': 'You move north into a corridor.',
            'new_location': 'corridor_north'
        })

        command = ParsedCommand(
            command_type=CommandType.MOVEMENT,
            action="go",
            direction="north"
        )

        response = await self.narrator.handle_command(command, self.sample_game_state)

        # Verify response from agent
        self.assertEqual(response.agent, "RoomDescriptor")
        self.assertIn("corridor", response.narrative)
        self.assertEqual(response.game_state_updates["location"], "corridor_north")
        self.assertTrue(response.success)

        # Verify agent was called
        self.mock_room_descriptor.handle_movement.assert_called_once_with(
            "dungeon_entrance", "north"
        )

    async def test_movement_with_blocked_path(self):
        """Test movement command when path is blocked."""
        # Setup mock for blocked movement
        self.mock_room_descriptor.handle_movement = AsyncMock(return_value={
            'success': False,
            'description': 'The way is blocked.',
            'new_location': None
        })

        command = ParsedCommand(
            command_type=CommandType.MOVEMENT,
            action="go",
            direction="south"
        )

        response = await self.narrator.handle_command(command, self.sample_game_state)

        # Verify blocked response
        self.assertEqual(response.agent, "RoomDescriptor")
        self.assertIn("cannot go south", response.narrative)
        self.assertFalse(response.success)
        self.assertTrue(response.metadata.get('blocked'))

    async def test_examination_with_room_descriptor_agent(self):
        """Test examination command integration with room_descriptor agent."""
        # Setup mock
        self.mock_room_descriptor.get_room_description = AsyncMock(
            return_value="You are in a dimly lit dungeon entrance."
        )

        command = ParsedCommand(
            command_type=CommandType.LOOK,
            action="look",
            target="around"
        )

        response = await self.narrator.handle_command(command, self.sample_game_state)

        # Verify response from agent
        self.assertEqual(response.agent, "RoomDescriptor")
        self.assertIn("dimly lit", response.narrative)
        self.assertTrue(response.success)

        # Verify agent was called
        self.mock_room_descriptor.get_room_description.assert_called_once_with(
            "dungeon_entrance"
        )

    async def test_pickup_item_with_inventory_manager_agent(self):
        """Test item pickup integration with inventory_manager agent."""
        # Setup mock
        self.mock_inventory_manager.pickup_item = AsyncMock(return_value={
            'success': True,
            'message': 'You pick up the golden sword.',
            'inventory_update': ['rusty_key', 'torch', 'golden_sword']
        })

        command = ParsedCommand(
            command_type=CommandType.PICKUP,
            action="take",
            target="golden_sword"
        )

        response = await self.narrator.handle_command(command, self.sample_game_state)

        # Verify response from agent
        self.assertEqual(response.agent, "InventoryManager")
        self.assertIn("golden sword", response.narrative)
        self.assertTrue(response.success)
        self.assertIn('golden_sword', response.game_state_updates['inventory'])

        # Verify agent was called
        self.mock_inventory_manager.pickup_item.assert_called_once_with(
            'golden_sword', ['rusty_key', 'torch']
        )

    async def test_talk_with_entity_manager_agent(self):
        """Test talk command integration with entity_manager agent."""
        # Setup mock
        self.mock_entity_manager.talk_to_entity = AsyncMock(return_value={
            'success': True,
            'message': 'You speak with the wise old wizard.',
            'dialogue': 'The wizard nods knowingly.',
            'state_changes': {'wizard_talked': True}
        })

        command = ParsedCommand(
            command_type=CommandType.TALK,
            action="talk",
            target="wizard"
        )

        response = await self.narrator.handle_command(command, self.sample_game_state)

        # Verify response from agent
        self.assertEqual(response.agent, "EntityManager")
        self.assertIn("wise old wizard", response.narrative)
        self.assertTrue(response.success)
        self.assertEqual(response.game_state_updates['wizard_talked'], True)

        # Verify agent was called
        self.mock_entity_manager.talk_to_entity.assert_called_once_with('wizard')

    async def test_agent_error_handling(self):
        """Test error handling when agent calls fail."""
        # Setup mock to raise exception
        self.mock_room_descriptor.handle_movement = AsyncMock(
            side_effect=Exception("Database connection error")
        )

        command = ParsedCommand(
            command_type=CommandType.MOVEMENT,
            action="go",
            direction="east"
        )

        response = await self.narrator.handle_command(command, self.sample_game_state)

        # Verify fallback behavior
        self.assertEqual(response.agent, "AdventureNarrator")
        self.assertIn("Agent error", response.narrative)
        self.assertIn("Database connection error", response.narrative)
        self.assertTrue(response.success)  # Fallback should still succeed

    async def test_no_agents_fallback(self):
        """Test fallback behavior when no agents are provided."""
        # Create narrator without agents
        narrator_no_agents = AdventureNarrator()

        command = ParsedCommand(
            command_type=CommandType.MOVEMENT,
            action="go",
            direction="west"
        )

        response = await narrator_no_agents.handle_command(command, self.sample_game_state)

        # Verify fallback behavior
        self.assertEqual(response.agent, "AdventureNarrator")
        self.assertIn("not yet implemented", response.narrative)
        self.assertTrue(response.success)


if __name__ == "__main__":
    unittest.main()
