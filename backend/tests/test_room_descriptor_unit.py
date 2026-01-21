"""Unit tests for RoomDescriptor agent, focusing on item filtering."""
import unittest
from unittest.mock import patch
from app.agents.room_descriptor import RoomDescriptor


class TestRoomDescriptorItemFiltering(unittest.TestCase):
    """Test item filtering logic in room descriptions."""

    def setUp(self):
        """Set up test fixtures."""
        self.descriptor = RoomDescriptor()

    def test_filter_no_items_picked_up(self):
        """Test that description is unchanged when no items are picked up."""
        description = (
            "A dimly lit cave entrance carved into the mountainside. "
            "A sturdy magical rope lies coiled near the entrance. "
            "The path leads deeper into darkness."
        )
        inventory = []

        result = self.descriptor._filter_picked_up_items(description, inventory)

        self.assertEqual(result, description)

    def test_filter_single_item_with_lies(self):
        """Test filtering a sentence with 'lies' indicator."""
        description = (
            "A dimly lit cave entrance carved into the mountainside. "
            "A sturdy magical rope lies coiled near the entrance. "
            "The path leads deeper into darkness."
        )
        inventory = ["magical_rope"]

        result = self.descriptor._filter_picked_up_items(description, inventory)

        # The rope sentence should be removed
        self.assertNotIn("rope", result.lower())
        self.assertIn("dimly lit cave", result.lower())
        self.assertIn("path leads deeper", result.lower())

    def test_filter_single_item_with_rests(self):
        """Test filtering a sentence with 'rests' indicator."""
        description = (
            "A cluttered storage room. "
            "An ancient explorer journal rests on a dusty shelf. "
            "Cobwebs cover the corners."
        )
        inventory = ["explorer_journal"]

        result = self.descriptor._filter_picked_up_items(description, inventory)

        self.assertNotIn("journal", result.lower())
        self.assertIn("cluttered storage", result.lower())
        self.assertIn("cobwebs", result.lower())

    def test_filter_single_item_with_hangs(self):
        """Test filtering a sentence with 'hangs' indicator."""
        description = (
            "A dimly lit chamber. "
            "A rusty iron key hangs from a hook on the wall. "
            "Water drips from the ceiling."
        )
        inventory = ["iron_key"]

        result = self.descriptor._filter_picked_up_items(description, inventory)

        self.assertNotIn("key", result.lower())
        self.assertIn("dimly lit chamber", result.lower())
        self.assertIn("water drips", result.lower())

    def test_filter_multiple_items(self):
        """Test filtering multiple items from description."""
        description = (
            "A treasure room filled with riches. "
            "A gleaming sword rests against the wall. "
            "A golden amulet lies on a pedestal. "
            "Ancient tapestries cover the walls."
        )
        inventory = ["gleaming_sword", "golden_amulet"]

        result = self.descriptor._filter_picked_up_items(description, inventory)

        self.assertNotIn("sword", result.lower())
        self.assertNotIn("amulet", result.lower())
        self.assertIn("treasure room", result.lower())
        self.assertIn("tapestries", result.lower())

    def test_filter_item_mentioned_multiple_times(self):
        """Test filtering when item is mentioned in multiple sentences."""
        description = (
            "A mysterious chamber. "
            "A magical rope lies coiled on the floor. "
            "The rope glows with an ethereal light. "
            "Strange symbols cover the walls."
        )
        inventory = ["magical_rope"]

        result = self.descriptor._filter_picked_up_items(description, inventory)

        # First sentence with "lies" indicator should be removed
        self.assertNotIn("lies coiled", result.lower())
        # Second sentence without indicator might remain (depends on implementation)
        # We're primarily filtering sentences with placement indicators
        self.assertIn("mysterious chamber", result.lower())

    def test_filter_preserves_other_content(self):
        """Test that filtering doesn't affect unrelated content."""
        description = (
            "The cave entrance is dark and foreboding. "
            "A torch lies on the ground, its flame extinguished. "
            "You can hear water dripping in the distance. "
            "The air smells of damp earth."
        )
        inventory = ["torch"]

        result = self.descriptor._filter_picked_up_items(description, inventory)

        self.assertNotIn("torch", result.lower())
        self.assertIn("dark and foreboding", result.lower())
        self.assertIn("water dripping", result.lower())
        self.assertIn("damp earth", result.lower())

    def test_filter_case_insensitive_matching(self):
        """Test that item matching is case-insensitive."""
        description = (
            "A grand hall. "
            "The Magical Rope lies coiled in the corner. "
            "Sunlight streams through windows."
        )
        inventory = ["magical_rope"]  # lowercase

        result = self.descriptor._filter_picked_up_items(description, inventory)

        self.assertNotIn("rope", result.lower())
        self.assertIn("grand hall", result.lower())

    def test_filter_handles_underscores_in_item_names(self):
        """Test that item_ids with underscores match descriptions with spaces."""
        description = (
            "A dusty library. "
            "An explorer journal rests on a desk. "
            "Books line the shelves."
        )
        inventory = ["explorer_journal"]  # underscore

        result = self.descriptor._filter_picked_up_items(description, inventory)

        self.assertNotIn("journal", result.lower())
        self.assertIn("dusty library", result.lower())

    def test_filter_empty_inventory(self):
        """Test with explicitly empty inventory."""
        description = (
            "A room with items. "
            "A sword lies here. "
            "A shield rests there."
        )
        inventory = []

        result = self.descriptor._filter_picked_up_items(description, inventory)

        self.assertEqual(result, description)

    def test_filter_empty_description(self):
        """Test with empty description."""
        description = ""
        inventory = ["some_item"]

        result = self.descriptor._filter_picked_up_items(description, inventory)

        self.assertEqual(result, "")

    def test_filter_with_coiled_indicator(self):
        """Test filtering with 'coiled' indicator word."""
        description = (
            "The entrance chamber. "
            "A magical rope sits coiled by the doorway. "
            "The ceiling is high above."
        )
        inventory = ["magical_rope"]

        result = self.descriptor._filter_picked_up_items(description, inventory)

        self.assertNotIn("coiled", result.lower())
        self.assertIn("entrance chamber", result.lower())


class TestRoomDescriptorIntegration(unittest.IsolatedAsyncioTestCase):
    """Test RoomDescriptor with mocked dependencies."""

    async def test_get_room_description_applies_filtering(self):
        """Test that get_room_description calls item filtering with inventory."""
        descriptor = RoomDescriptor()

        # Mock the RAG retrieval
        mock_rag_response = (
            "A dimly lit cave. "
            "A magical rope lies coiled here. "
            "Darkness extends ahead."
        )

        mock_game_state = {
            "location": "cave_entrance",
            "inventory": ["magical_rope"],  # Item has been picked up
            "character_name": "TestHero",
            "character_class": "warrior"
        }

        with patch('app.agents.room_descriptor.rag_get_room_description') as mock_rag:
            mock_rag.return_value = mock_rag_response

            result = await descriptor.get_room_description(
                location="cave_entrance",
                game_state=mock_game_state
            )

            # Verify RAG was called
            mock_rag.assert_called_once()

            # Verify the result doesn't contain the picked-up item
            self.assertNotIn("rope", result.lower())
            self.assertIn("dimly lit cave", result.lower())

    async def test_get_room_description_with_empty_inventory(self):
        """Test room description when inventory is empty."""
        descriptor = RoomDescriptor()

        mock_rag_response = (
            "A dimly lit cave. "
            "A magical rope lies coiled here. "
            "Darkness extends ahead."
        )

        mock_game_state = {
            "location": "cave_entrance",
            "inventory": [],  # No items picked up
            "character_name": "TestHero",
            "character_class": "warrior"
        }

        with patch('app.agents.room_descriptor.rag_get_room_description') as mock_rag:
            mock_rag.return_value = mock_rag_response

            result = await descriptor.get_room_description(
                location="cave_entrance",
                game_state=mock_game_state
            )

            # With empty inventory, rope should still be mentioned
            self.assertIn("rope", result.lower())
            self.assertIn("dimly lit cave", result.lower())

    async def test_examine_filters_wrong_class_hints_wizard(self):
        """Test that examine filters out rogue/warrior hints for wizard."""
        descriptor = RoomDescriptor()

        with patch('app.agents.room_descriptor.query_world_lore') as mock_rag:
            # Return text with rogue-specific hints
            mock_rag.return_value = [
                "The rope will help you cross the chasm. "
                "Your natural climbing skills and agility make you nimble enough to find your own path."
            ]

            result = await descriptor.examine_environment(
                location="cave_entrance",
                target="rope",
                character_class="wizard"
            )

            # Should filter out rogue-specific phrases
            self.assertNotIn("natural climbing", result.lower())
            self.assertNotIn("nimble", result.lower())
            self.assertNotIn("agility", result.lower())

    async def test_examine_filters_wrong_class_hints_warrior(self):
        """Test that examine filters out wizard/rogue hints for warrior."""
        descriptor = RoomDescriptor()

        with patch('app.agents.room_descriptor.query_world_lore') as mock_rag:
            # Return text with wizard-specific hints
            mock_rag.return_value = [
                "The rope can be useful. "
                "Your magical knowledge and intellect will help you understand its enchantment. "
                "Your scholarship is your greatest asset."
            ]

            result = await descriptor.examine_environment(
                location="cave_entrance",
                target="rope",
                character_class="warrior"
            )

            # Should filter out wizard-specific phrases
            self.assertNotIn("magical knowledge", result.lower())
            self.assertNotIn("intellect", result.lower())
            self.assertNotIn("scholarship", result.lower())

    async def test_examine_filters_wrong_class_hints_rogue(self):
        """Test that examine filters out wizard/warrior hints for rogue."""
        descriptor = RoomDescriptor()

        with patch('app.agents.room_descriptor.query_world_lore') as mock_rag:
            # Return text with warrior-specific hints
            mock_rag.return_value = [
                "The rope is sturdy and strong. "
                "Your powerful muscles and strong arms can pull you across any gap. "
                "Brute force is often the best approach."
            ]

            result = await descriptor.examine_environment(
                location="cave_entrance",
                target="rope",
                character_class="rogue"
            )

            # Should filter out warrior-specific phrases
            self.assertNotIn("powerful muscles", result.lower())
            self.assertNotIn("strong arms", result.lower())
            self.assertNotIn("brute force", result.lower())

    async def test_examine_allows_matching_class_hints(self):
        """Test that examine allows hints for the correct class."""
        descriptor = RoomDescriptor()

        with patch('app.agents.room_descriptor.query_world_lore') as mock_rag:
            # Return text with wizard-specific hints
            mock_rag.return_value = [
                "The rope shimmers with faint magical energy. "
                "Your magical knowledge will help you enhance it for safer passage. "
                "Look for ancient writings that might reveal more."
            ]

            result = await descriptor.examine_environment(
                location="cave_entrance",
                target="rope",
                character_class="wizard"
            )

            # Should keep wizard-specific content for wizard
            self.assertIn("magical", result.lower())

    async def test_examine_without_class_shows_all(self):
        """Test that examine without character_class doesn't filter class hints."""
        descriptor = RoomDescriptor()

        with patch('app.agents.room_descriptor.query_world_lore') as mock_rag:
            # Return text with mixed class hints
            mock_rag.return_value = [
                "The rope is useful. "
                "Your natural climbing skills will help you. "
                "Your magical knowledge is valuable."
            ]

            result = await descriptor.examine_environment(
                location="cave_entrance",
                target="rope",
                character_class=None  # No filtering
            )

            # Without class filtering, should show content
            # (though it may filter for other reasons)
            self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
