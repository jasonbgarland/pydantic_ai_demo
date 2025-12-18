"""Unit tests for AdventureNarrator command parsing and orchestration."""
import unittest
from app.agents.adventure_narrator import (
    AdventureNarrator, CommandType, ParsedCommand, GameResponse
)


class TestAdventureNarratorParsing(unittest.TestCase):
    """Test command parsing functionality of AdventureNarrator."""

    def setUp(self):
        """Set up test fixtures."""
        self.narrator = AdventureNarrator()

    def test_movement_commands(self):
        """Test parsing of movement commands."""
        # Direct direction
        result = self.narrator.parse_command("north")
        self.assertEqual(result.command_type, CommandType.MOVEMENT)
        self.assertEqual(result.action, "go")
        self.assertEqual(result.direction, "north")
        self.assertGreaterEqual(result.confidence, 0.8)

        # Go + direction
        result = self.narrator.parse_command("go south")
        self.assertEqual(result.command_type, CommandType.MOVEMENT)
        self.assertEqual(result.action, "go")
        self.assertEqual(result.direction, "south")
        self.assertGreaterEqual(result.confidence, 0.9)

        # Walk + direction
        result = self.narrator.parse_command("walk east")
        self.assertEqual(result.command_type, CommandType.MOVEMENT)
        self.assertEqual(result.action, "walk")
        self.assertEqual(result.direction, "east")

    def test_examine_commands(self):
        """Test parsing of examination commands."""
        # Simple examine
        result = self.narrator.parse_command("examine sword")
        self.assertEqual(result.command_type, CommandType.EXAMINE)
        self.assertEqual(result.action, "examine")
        self.assertEqual(result.target, "sword")

        # Look at
        result = self.narrator.parse_command("look at door")
        self.assertEqual(result.command_type, CommandType.EXAMINE)
        self.assertEqual(result.action, "examine")
        self.assertEqual(result.target, "door")

        # Look around
        result = self.narrator.parse_command("look")
        self.assertEqual(result.command_type, CommandType.LOOK)
        self.assertEqual(result.action, "look")
        self.assertEqual(result.target, "around")

    def test_item_commands(self):
        """Test parsing of item interaction commands."""
        # Pickup
        result = self.narrator.parse_command("take gold coin")
        self.assertEqual(result.command_type, CommandType.PICKUP)
        self.assertEqual(result.action, "take")
        self.assertEqual(result.target, "gold coin")

        # Drop
        result = self.narrator.parse_command("drop rusty key")
        self.assertEqual(result.command_type, CommandType.DROP)
        self.assertEqual(result.action, "drop")
        self.assertEqual(result.target, "rusty key")

        # Use
        result = self.narrator.parse_command("use magic potion")
        self.assertEqual(result.command_type, CommandType.USE)
        self.assertEqual(result.action, "use")
        self.assertEqual(result.target, "magic potion")

    def test_entity_commands(self):
        """Test parsing of entity interaction commands."""
        # Talk
        result = self.narrator.parse_command("talk to wizard")
        self.assertEqual(result.command_type, CommandType.TALK)
        self.assertEqual(result.action, "talk")
        self.assertEqual(result.target, "to wizard")

        # Attack
        result = self.narrator.parse_command("attack goblin")
        self.assertEqual(result.command_type, CommandType.ATTACK)
        self.assertEqual(result.action, "attack")
        self.assertEqual(result.target, "goblin")

    def test_meta_commands(self):
        """Test parsing of meta/UI commands."""
        # Inventory
        result = self.narrator.parse_command("inventory")
        self.assertEqual(result.command_type, CommandType.INVENTORY)
        self.assertEqual(result.action, "inventory")

    def test_unknown_commands(self):
        """Test parsing of unrecognized commands."""
        # Empty command
        result = self.narrator.parse_command("")
        self.assertEqual(result.command_type, CommandType.UNKNOWN)
        self.assertEqual(result.confidence, 0.0)

        # Nonsense command
        result = self.narrator.parse_command("flibber jibber")
        self.assertEqual(result.command_type, CommandType.UNKNOWN)
        self.assertEqual(result.action, "flibber jibber")
        self.assertLess(result.confidence, 0.5)

    def test_command_confidence_levels(self):
        """Test that confidence levels are appropriate."""
        # High confidence: explicit "go north"
        result = self.narrator.parse_command("go north")
        self.assertGreaterEqual(result.confidence, 0.9)

        # Medium confidence: single action word
        result = self.narrator.parse_command("examine")
        self.assertGreaterEqual(result.confidence, 0.7)

        # Low confidence: unknown command
        result = self.narrator.parse_command("xyzzy magic word")
        self.assertLess(result.confidence, 0.5)


class TestAdventureNarratorOrchestration(unittest.IsolatedAsyncioTestCase):
    """Test orchestration functionality of AdventureNarrator."""

    def setUp(self):
        """Set up test fixtures."""
        self.narrator = AdventureNarrator()
        self.sample_game_state = {
            "location": "dungeon_entrance",
            "inventory": ["rusty_key", "torch"],
            "discovered": ["dungeon_entrance"],
            "turn_count": 5
        }

    async def test_handle_movement_command(self):
        """Test handling of movement commands."""
        command = ParsedCommand(
            command_type=CommandType.MOVEMENT,
            action="go",
            direction="north"
        )

        response = await self.narrator.handle_command(command, self.sample_game_state)

        self.assertIsInstance(response, GameResponse)
        self.assertEqual(response.agent, "AdventureNarrator")
        self.assertIn("north", response.narrative)
        self.assertIn("dungeon_entrance", response.narrative)
        self.assertTrue(response.success)
        self.assertEqual(response.game_state_updates["location"], "dungeon_entrance_north")
        self.assertEqual(response.metadata["direction"], "north")

    async def test_handle_examination_command(self):
        """Test handling of examination commands."""
        command = ParsedCommand(
            command_type=CommandType.EXAMINE,
            action="examine",
            target="door"
        )

        response = await self.narrator.handle_command(command, self.sample_game_state)

        self.assertIsInstance(response, GameResponse)
        self.assertEqual(response.agent, "AdventureNarrator")
        self.assertIn("door", response.narrative)
        self.assertTrue(response.success)
        self.assertEqual(response.metadata["examined"], "door")

    async def test_handle_look_around_command(self):
        """Test handling of 'look around' commands."""
        command = ParsedCommand(
            command_type=CommandType.LOOK,
            action="look",
            target="around"
        )

        response = await self.narrator.handle_command(command, self.sample_game_state)

        self.assertIsInstance(response, GameResponse)
        self.assertIn("look around", response.narrative)
        self.assertIn("unknown place", response.narrative)
        self.assertTrue(response.success)
        self.assertEqual(response.metadata["examined"], "around")

    async def test_handle_item_pickup_command(self):
        """Test handling of item pickup commands."""
        command = ParsedCommand(
            command_type=CommandType.PICKUP,
            action="take",
            target="gold coin"
        )

        response = await self.narrator.handle_command(command, self.sample_game_state)

        self.assertIsInstance(response, GameResponse)
        self.assertIn("take", response.narrative)
        self.assertIn("gold coin", response.narrative)
        self.assertTrue(response.success)
        self.assertEqual(response.metadata["item_action"], "take")
        self.assertEqual(response.metadata["target"], "gold coin")

    async def test_handle_item_drop_command(self):
        """Test handling of item drop commands."""
        command = ParsedCommand(
            command_type=CommandType.DROP,
            action="drop",
            target="torch"
        )

        response = await self.narrator.handle_command(command, self.sample_game_state)

        self.assertIsInstance(response, GameResponse)
        self.assertIn("drop", response.narrative)
        self.assertIn("torch", response.narrative)
        self.assertTrue(response.success)

    async def test_handle_item_use_command(self):
        """Test handling of item use commands."""
        command = ParsedCommand(
            command_type=CommandType.USE,
            action="use",
            target="rusty_key"
        )

        response = await self.narrator.handle_command(command, self.sample_game_state)

        self.assertIsInstance(response, GameResponse)
        self.assertIn("use", response.narrative)
        self.assertIn("rusty_key", response.narrative)
        self.assertTrue(response.success)

    async def test_handle_talk_command(self):
        """Test handling of talk commands."""
        command = ParsedCommand(
            command_type=CommandType.TALK,
            action="talk",
            target="to wizard"
        )

        response = await self.narrator.handle_command(command, self.sample_game_state)

        self.assertIsInstance(response, GameResponse)
        self.assertIn("talk", response.narrative)
        self.assertIn("to wizard", response.narrative)
        self.assertTrue(response.success)
        self.assertEqual(response.metadata["entity_action"], "talk")

    async def test_handle_attack_command(self):
        """Test handling of attack commands."""
        command = ParsedCommand(
            command_type=CommandType.ATTACK,
            action="attack",
            target="goblin"
        )

        response = await self.narrator.handle_command(command, self.sample_game_state)

        self.assertIsInstance(response, GameResponse)
        self.assertIn("attack", response.narrative)
        self.assertIn("goblin", response.narrative)
        self.assertTrue(response.success)

    async def test_handle_inventory_command(self):
        """Test handling of inventory commands."""
        command = ParsedCommand(
            command_type=CommandType.INVENTORY,
            action="inventory"
        )

        response = await self.narrator.handle_command(command, self.sample_game_state)

        self.assertIsInstance(response, GameResponse)
        self.assertIn("rusty_key", response.narrative)
        self.assertIn("torch", response.narrative)
        self.assertTrue(response.success)
        self.assertEqual(response.metadata["inventory"], ["rusty_key", "torch"])

    async def test_handle_inventory_command_empty(self):
        """Test handling of inventory commands when inventory is empty."""
        empty_state = {**self.sample_game_state, "inventory": []}
        command = ParsedCommand(
            command_type=CommandType.INVENTORY,
            action="inventory"
        )

        response = await self.narrator.handle_command(command, empty_state)

        self.assertIn("inventory is empty", response.narrative)
        self.assertEqual(response.metadata["inventory"], [])

    async def test_handle_unknown_command(self):
        """Test handling of unknown commands."""
        command = ParsedCommand(
            command_type=CommandType.UNKNOWN,
            action="flibber jibber"
        )

        response = await self.narrator.handle_command(command, self.sample_game_state)

        self.assertIsInstance(response, GameResponse)
        self.assertIn("don't understand", response.narrative)
        self.assertIn("flibber jibber", response.narrative)
        self.assertFalse(response.success)


if __name__ == "__main__":
    unittest.main()
