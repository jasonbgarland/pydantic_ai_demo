"""Unit tests for game session management with mocked external dependencies."""
import unittest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport

from app.main import app


class TestSessionsUnit(unittest.IsolatedAsyncioTestCase):
    """Unit tests for game session functionality with mocked dependencies."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        # Create HTTPX AsyncClient with app transport
        self.client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    async def asyncTearDown(self):
        """Clean up test fixtures."""
        await self.client.aclose()

    @patch('app.main.redis_client')
    @patch('app.main.create_session')
    async def test_start_game_creates_session_with_character(self, mock_create_session, _mock_redis):
        """Test that starting a game creates a session with proper character data."""
        # Mock the session creation
        mock_session = {
            "game_id": "test-game-123",
            "character": {
                "name": "TestWizard",
                "character_class": "wizard",
                "level": 1,
                "hp": 20
            },
            "location": "cave_entrance"
        }
        mock_create_session.return_value = mock_session

        response = await self.client.post("/game/start",
                                        json={"name": "TestWizard", "character_class": "wizard"})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["game_id"], "test-game-123")
        self.assertEqual(data["session"]["character"]["name"], "TestWizard")
        self.assertEqual(data["session"]["character"]["character_class"], "wizard")

        # Verify create_session was called with proper character data (classes are cosmetic)
        mock_create_session.assert_called_once()
        call_args = mock_create_session.call_args[0][0]  # First argument (character)
        self.assertEqual(call_args["name"], "TestWizard")
        self.assertEqual(call_args["character_class"], "wizard")
        self.assertEqual(call_args["hp"], 20)  # HP is always 20 (no class differences)

    @patch('app.main.get_session')
    @patch('app.main.save_session')
    async def test_process_command_increments_turn_and_saves(self, mock_save_session, mock_get_session):
        """Test that processing commands increments turn count and saves session."""
        # Mock existing session
        mock_session = {
            "game_id": "test-game-123",
            "turn_count": 0,
            "character": {"name": "TestChar"},
            "history": []
        }
        mock_get_session.return_value = mock_session
        mock_save_session.return_value = None

        response = await self.client.post("/game/test-game-123/command",
                                        json={"command": "look"})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["turn"], 1)
        # Should get actual game narrative, not placeholder
        self.assertIn("response", data)
        self.assertIsInstance(data["response"], str)
        self.assertGreater(len(data["response"]), 0)

        # Verify get_session was called with correct game_id
        mock_get_session.assert_called_once_with("test-game-123")

        # Verify save_session was called with updated session
        mock_save_session.assert_called_once()
        saved_session = mock_save_session.call_args[0][1]  # Second argument (session)
        self.assertEqual(saved_session["turn_count"], 1)
        self.assertEqual(len(saved_session["history"]), 1)
        self.assertEqual(saved_session["history"][0]["command"], "look")

    @patch('app.main.get_session')
    async def test_get_game_state_returns_session(self, mock_get_session):
        """Test that get_game_state returns the session from Redis."""
        mock_session = {
            "game_id": "test-game-123",
            "character": {"name": "TestChar"},
            "location": "dungeon_entrance"
        }
        mock_get_session.return_value = mock_session

        response = await self.client.get("/game/test-game-123/state")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["game_id"], "test-game-123")
        self.assertEqual(data["character"]["name"], "TestChar")

        mock_get_session.assert_called_once_with("test-game-123")

    @patch('app.main.get_session')
    async def test_get_game_state_not_found(self, mock_get_session):
        """Test error handling when session is not found."""
        mock_get_session.return_value = None

        response = await self.client.get("/game/nonexistent-game/state")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["error"], "session_not_found")
        self.assertEqual(data["message"], "Game session not found")

    @patch('app.main.get_session')
    async def test_process_command_session_not_found(self, mock_get_session):
        """Test command processing when session doesn't exist."""
        mock_get_session.return_value = None

        response = await self.client.post("/game/nonexistent-game/command",
                                        json={"command": "look"})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["error"], "session_not_found")


if __name__ == "__main__":
    unittest.main()
