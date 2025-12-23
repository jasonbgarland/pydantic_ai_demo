"""Integration tests for the full command pipeline with RAG integration."""
import unittest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport

from app.main import app


class TestCommandPipelineRAG(unittest.IsolatedAsyncioTestCase):
    """Test the full command pipeline with AdventureNarrator + RoomDescriptor + RAG."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        self.client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    async def asyncTearDown(self):
        """Clean up test fixtures."""
        await self.client.aclose()

    @patch('app.main.redis_client')
    async def test_look_command_uses_rag(self, mock_redis):
        """Test that 'look' commands trigger RAG-powered room descriptions."""
        # Mock Redis to return a test session
        mock_redis.get = AsyncMock(return_value='{"game_id": "test-123", "location": "Cave Entrance", "inventory": [], "visited_rooms": [], "turn_count": 0}')
        mock_redis.setex = AsyncMock()

        # Send a 'look' command
        response = await self.client.post(
            "/game/test-123/command",
            json={"command": "look around"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify response structure
        self.assertIn("response", data)
        self.assertIn("agent", data)
        self.assertEqual(data["success"], True)

        # Verify RoomDescriptor was used (it should generate the response)
        self.assertEqual(data["agent"], "RoomDescriptor")

        # Response should contain rich description (RAG-enhanced)
        narrative = data["response"]
        self.assertGreater(len(narrative), 50, "Description should be detailed")

    @patch('app.main.redis_client')
    async def test_examine_command_uses_rag(self, mock_redis):
        """Test that 'examine' commands trigger RAG queries for specific objects."""
        # Mock Redis
        mock_redis.get = AsyncMock(return_value='{"game_id": "test-456", "location": "Cave Entrance", "inventory": [], "visited_rooms": [], "turn_count": 0}')
        mock_redis.setex = AsyncMock()

        # Examine a specific object
        response = await self.client.post(
            "/game/test-456/command",
            json={"command": "examine walls"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Should get a response from RoomDescriptor
        self.assertEqual(data["agent"], "RoomDescriptor")
        self.assertEqual(data["success"], True)

        # Metadata should include what was examined
        self.assertIn("metadata", data)
        self.assertEqual(data["metadata"].get("examined"), "walls")

    @patch('app.main.redis_client')
    async def test_movement_command_with_rag(self, mock_redis):
        """Test that movement commands work and trigger new room descriptions via RAG."""
        # Mock Redis
        mock_redis.get = AsyncMock(return_value='{"game_id": "test-789", "location": "Cave Entrance", "inventory": [], "visited_rooms": [], "turn_count": 0}')
        mock_redis.setex = AsyncMock()

        # Try to move north
        response = await self.client.post(
            "/game/test-789/command",
            json={"command": "go north"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Movement command should be handled
        self.assertIn("response", data)

        # RoomDescriptor handles movement
        self.assertIn(data["agent"], ["RoomDescriptor", "AdventureNarrator"])

        # Response narrative should describe the movement
        self.assertIn("move", data["response"].lower())

    @patch('app.main.redis_client')
    async def test_unknown_command_fallback(self, mock_redis):
        """Test that unknown commands have graceful fallback (no RAG needed)."""
        # Mock Redis
        mock_redis.get = AsyncMock(return_value='{"game_id": "test-999", "location": "Cave Entrance", "inventory": [], "visited_rooms": [], "turn_count": 0}')
        mock_redis.setex = AsyncMock()

        # Send an unrecognized command
        response = await self.client.post(
            "/game/test-999/command",
            json={"command": "dance a jig"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Should fail gracefully
        self.assertEqual(data["success"], False)
        self.assertIn("understand", data["response"].lower())

    @patch('app.main.redis_client')
    async def test_command_pipeline_updates_session(self, mock_redis):
        """Test that commands update the session state correctly."""
        session_data = '{"game_id": "test-session", "location": "Cave Entrance", "inventory": [], "visited_rooms": [], "turn_count": 5}'
        mock_redis.get = AsyncMock(return_value=session_data)
        mock_redis.set = AsyncMock()

        response = await self.client.post(
            "/game/test-session/command",
            json={"command": "look"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Turn count should increment
        self.assertEqual(data["turn"], 6)

        # Session should be saved (Redis set called)
        mock_redis.set.assert_called_once()


if __name__ == '__main__':
    unittest.main()
