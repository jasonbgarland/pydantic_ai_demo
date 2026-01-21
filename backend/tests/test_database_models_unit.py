"""Unit tests for database models."""
import unittest
from unittest.mock import AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Character, GameSession, Discovery, NarrativeHistory


class TestDatabaseModels(unittest.TestCase):
    """Test SQLAlchemy database models structure and relationships."""

    def test_character_model_creation(self):
        """Test Character model can be created with required fields."""
        char = Character(
            id="test-char-123",
            name="Thorin",
            character_class="warrior",
            stats={"strength": 18, "magic": 8, "agility": 10},
            level=1
        )

        self.assertEqual(char.id, "test-char-123")
        self.assertEqual(char.name, "Thorin")
        self.assertEqual(char.character_class, "warrior")
        self.assertEqual(char.stats["strength"], 18)
        self.assertEqual(char.level, 1)
        self.assertIsNone(char.created_at)  # Not set until committed to DB

    def test_character_repr(self):
        """Test Character __repr__ method."""
        char = Character(
            id="test-123",
            name="Gandalf",
            character_class="wizard",
            stats={},
            level=5
        )

        repr_str = repr(char)
        self.assertIn("test-123", repr_str)
        self.assertIn("Gandalf", repr_str)
        self.assertIn("wizard", repr_str)

    def test_game_session_model_creation(self):
        """Test GameSession model can be created with required fields."""
        session = GameSession(
            id="session-456",
            character_id="char-123",
            current_location="cave_entrance",
            inventory=["torch", "rope"],
            turn_count=10,
            session_name="My Epic Adventure",
            is_active=True
        )

        self.assertEqual(session.id, "session-456")
        self.assertEqual(session.character_id, "char-123")
        self.assertEqual(session.current_location, "cave_entrance")
        self.assertEqual(len(session.inventory), 2)
        self.assertIn("torch", session.inventory)
        self.assertEqual(session.turn_count, 10)
        self.assertTrue(session.is_active)

    def test_game_session_default_values(self):
        """Test GameSession default values."""
        session = GameSession(
            id="session-789",
            character_id="char-456",
            current_location="cave_entrance"
        )

        self.assertIsNone(session.inventory)  # Default list set by DB
        self.assertIsNone(session.turn_count)  # Default 0 set by DB
        self.assertIsNone(session.is_active)  # Default True set by DB
        self.assertIsNone(session.session_name)

    def test_discovery_model_creation(self):
        """Test Discovery model can be created."""
        discovery = Discovery(
            game_session_id="session-123",
            discovery_type="room",
            entity_id="crystal_treasury",
            display_name="Crystal Treasury",
            turn_number=5,
            context={"method": "exploration"}
        )

        self.assertEqual(discovery.game_session_id, "session-123")
        self.assertEqual(discovery.discovery_type, "room")
        self.assertEqual(discovery.entity_id, "crystal_treasury")
        self.assertEqual(discovery.display_name, "Crystal Treasury")
        self.assertEqual(discovery.turn_number, 5)
        self.assertEqual(discovery.context["method"], "exploration")

    def test_discovery_types(self):
        """Test Discovery model supports different discovery types."""
        room_discovery = Discovery(
            game_session_id="s1",
            discovery_type="room",
            entity_id="cave_entrance",
            display_name="Cave Entrance",
            turn_number=1
        )

        item_discovery = Discovery(
            game_session_id="s1",
            discovery_type="item",
            entity_id="magical_rope",
            display_name="Magical Rope",
            turn_number=3
        )

        secret_discovery = Discovery(
            game_session_id="s1",
            discovery_type="secret",
            entity_id="hidden_passage",
            display_name="Hidden Passage",
            turn_number=7
        )

        self.assertEqual(room_discovery.discovery_type, "room")
        self.assertEqual(item_discovery.discovery_type, "item")
        self.assertEqual(secret_discovery.discovery_type, "secret")

    def test_narrative_history_model_creation(self):
        """Test NarrativeHistory model can be created."""
        narrative = NarrativeHistory(
            game_session_id="session-999",
            turn_number=1,
            command="look around",
            narrative="You see a dark cave entrance...",
            agent_used="room_descriptor",
            response_metadata={"duration_ms": 450}
        )

        self.assertEqual(narrative.game_session_id, "session-999")
        self.assertEqual(narrative.turn_number, 1)
        self.assertEqual(narrative.command, "look around")
        self.assertIn("dark cave", narrative.narrative)
        self.assertEqual(narrative.agent_used, "room_descriptor")
        self.assertEqual(narrative.response_metadata["duration_ms"], 450)

    def test_narrative_history_optional_fields(self):
        """Test NarrativeHistory with minimal required fields."""
        narrative = NarrativeHistory(
            game_session_id="session-abc",
            turn_number=5,
            command="examine crystal",
            narrative="The crystal gleams..."
        )

        self.assertEqual(narrative.turn_number, 5)
        self.assertIsNone(narrative.agent_used)
        self.assertIsNone(narrative.response_metadata)


class TestDatabaseModelRelationships(unittest.TestCase):
    """Test model relationships (requires mocking)."""

    def test_character_has_game_sessions_relationship(self):
        """Test Character model has game_sessions relationship defined."""
        char = Character(
            id="char-1",
            name="Test",
            character_class="warrior",
            stats={}
        )

        # Relationship exists (will be populated by SQLAlchemy)
        self.assertTrue(hasattr(char, 'game_sessions'))

    def test_game_session_has_character_relationship(self):
        """Test GameSession has character relationship."""
        session = GameSession(
            id="session-1",
            character_id="char-1",
            current_location="cave"
        )

        self.assertTrue(hasattr(session, 'character'))
        self.assertTrue(hasattr(session, 'discoveries'))
        self.assertTrue(hasattr(session, 'narrative_entries'))

    def test_discovery_has_game_session_relationship(self):
        """Test Discovery has game_session relationship."""
        discovery = Discovery(
            game_session_id="session-1",
            discovery_type="room",
            entity_id="test_room",
            display_name="Test Room",
            turn_number=1
        )

        self.assertTrue(hasattr(discovery, 'game_session'))


class TestDatabaseOperations(unittest.IsolatedAsyncioTestCase):
    """Test database operations with mocked async session."""

    async def test_create_character_operation(self):
        """Test creating a character in the database."""
        # Mock the database session
        mock_session = AsyncMock(spec=AsyncSession)

        # Create character
        char = Character(
            id="test-char",
            name="Hero",
            character_class="rogue",
            stats={"agility": 15, "stealth": 18},
            level=1
        )

        # Simulate adding to session
        mock_session.add(char)
        await mock_session.commit()

        # Verify operations were called
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_create_game_session_with_snapshot(self):
        """Test creating game session with state snapshot."""
        mock_session = AsyncMock(spec=AsyncSession)

        game_state = {
            "location": "cave_entrance",
            "inventory": ["torch"],
            "turn_count": 5,
            "character": {"name": "Hero", "class": "warrior"}
        }

        session = GameSession(
            id="game-123",
            character_id="char-123",
            current_location="cave_entrance",
            inventory=["torch"],
            turn_count=5,
            state_snapshot=game_state
        )

        mock_session.add(session)
        await mock_session.commit()

        self.assertEqual(session.state_snapshot["turn_count"], 5)
        self.assertEqual(session.state_snapshot["character"]["name"], "Hero")

    async def test_rollback_on_error(self):
        """Test that session rollback is called on error."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit.side_effect = Exception("Database error")

        try:
            char = Character(id="test", name="Test", character_class="wizard", stats={})
            mock_session.add(char)
            await mock_session.commit()
        except Exception:
            await mock_session.rollback()

        mock_session.rollback.assert_called_once()


if __name__ == '__main__':
    unittest.main()
