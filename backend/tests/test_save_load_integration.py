"""Integration tests for save/load game endpoints."""
import os
import unittest
from httpx import AsyncClient, ASGITransport

# Set environment variables before importing app
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
os.environ['DATABASE_URL'] = 'postgresql://adventure:development_password@localhost:5432/adventure_engine'

from app.main import app


@unittest.skipUnless(os.getenv('RUN_INTEGRATION_TESTS'), 'Integration tests disabled')
class TestSaveLoadIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for PostgreSQL save/load endpoints."""

    async def asyncSetUp(self):
        """Set up test client and create a test game session."""
        self.transport = ASGITransport(app=app)
        self.client = AsyncClient(transport=self.transport, base_url="http://test")

        # Start a test game session (creates character internally)
        start_game_response = await self.client.post(
            "/game/start",
            json={"name": "TestHero", "character_class": "warrior"}
        )
        self.assertEqual(start_game_response.status_code, 200)
        self.test_session = start_game_response.json()
        self.game_id = self.test_session["game_id"]

        # Execute a few commands to generate game state
        await self.client.post(
            f"/game/{self.game_id}/command",
            json={"command": "look around"}
        )
        await self.client.post(
            f"/game/{self.game_id}/command",
            json={"command": "examine cave"}
        )

    async def asyncTearDown(self):
        """Clean up test client."""
        await self.client.aclose()

    async def test_save_game_creates_database_record(self):
        """Test that saving a game creates a PostgreSQL record."""
        # Save the game
        save_response = await self.client.post(
            f"/game/{self.game_id}/save",
            json={"session_name": "Test Save"}
        )

        self.assertEqual(save_response.status_code, 200)
        save_data = save_response.json()

        # Verify response structure
        self.assertIn("game_id", save_data)
        self.assertIn("character_id", save_data)
        self.assertIn("session_name", save_data)
        self.assertIn("saved_at", save_data)

        self.assertEqual(save_data["game_id"], self.game_id)
        self.assertEqual(save_data["session_name"], "Test Save")

    async def test_save_game_without_session_name(self):
        """Test saving game with auto-generated session name."""
        save_response = await self.client.post(
            f"/game/{self.game_id}/save",
            json={}
        )

        self.assertEqual(save_response.status_code, 200)
        save_data = save_response.json()

        # Should have auto-generated name with timestamp
        self.assertIn("Adventure -", save_data["session_name"])

    async def test_save_nonexistent_game_returns_error(self):
        """Test saving a non-existent game returns error."""
        fake_game_id = "fake-game-id-999"

        save_response = await self.client.post(
            f"/game/{fake_game_id}/save",
            json={"session_name": "Should Fail"}
        )

        self.assertEqual(save_response.status_code, 200)
        save_data = save_response.json()

        self.assertIn("error", save_data)
        self.assertEqual(save_data["error"], "session_not_found")

    async def test_list_saved_games(self):
        """Test listing all saved games."""
        # Save the current game
        await self.client.post(
            f"/game/{self.game_id}/save",
            json={"session_name": "List Test Save"}
        )

        # List saves
        list_response = await self.client.get("/game/saves")

        self.assertEqual(list_response.status_code, 200)
        list_data = list_response.json()

        # Verify response structure
        self.assertIn("saves", list_data)
        self.assertIn("count", list_data)
        self.assertIsInstance(list_data["saves"], list)
        self.assertGreater(list_data["count"], 0)

        # Find our save in the list
        our_save = next(
            (s for s in list_data["saves"] if s["game_id"] == self.game_id),
            None
        )
        self.assertIsNotNone(our_save)
        self.assertEqual(our_save["session_name"], "List Test Save")
        self.assertEqual(our_save["character_name"], "TestHero")
        self.assertEqual(our_save["character_class"], "warrior")

    async def test_load_saved_game(self):
        """Test loading a saved game from PostgreSQL into Redis."""
        # Save the game first
        save_response = await self.client.post(
            f"/game/{self.game_id}/save",
            json={"session_name": "Load Test"}
        )
        self.assertEqual(save_response.status_code, 200)

        # Load the game
        load_response = await self.client.post(f"/game/{self.game_id}/load")

        self.assertEqual(load_response.status_code, 200)
        load_data = load_response.json()

        # Verify response
        self.assertTrue(load_data["success"])
        self.assertEqual(load_data["game_id"], self.game_id)
        self.assertIn("session", load_data)
        self.assertIn("Loaded save: Load Test", load_data["message"])

        # Verify session was restored
        session = load_data["session"]
        self.assertEqual(session["game_id"], self.game_id)
        self.assertIn("character", session)
        self.assertEqual(session["character"]["name"], "TestHero")

    async def test_load_nonexistent_save_returns_error(self):
        """Test loading a non-existent save returns error."""
        fake_game_id = "nonexistent-save-999"

        load_response = await self.client.post(f"/game/{fake_game_id}/load")

        self.assertEqual(load_response.status_code, 200)
        load_data = load_response.json()

        self.assertIn("error", load_data)
        self.assertEqual(load_data["error"], "save_not_found")

    async def test_delete_saved_game(self):
        """Test deleting (soft delete) a saved game."""
        # Save the game first
        await self.client.post(
            f"/game/{self.game_id}/save",
            json={"session_name": "Delete Test"}
        )

        # Delete the save
        delete_response = await self.client.delete(f"/game/{self.game_id}/save")

        self.assertEqual(delete_response.status_code, 200)
        delete_data = delete_response.json()

        self.assertTrue(delete_data["success"])
        self.assertEqual(delete_data["game_id"], self.game_id)

        # Verify it's no longer in the active saves list
        list_response = await self.client.get("/game/saves")
        list_data = list_response.json()

        deleted_save = next(
            (s for s in list_data["saves"] if s["game_id"] == self.game_id),
            None
        )
        self.assertIsNone(deleted_save)  # Should not appear in active saves

    async def test_save_preserves_game_state(self):
        """Test that saving and loading preserves complete game state."""
        # Get current session state
        state_response = await self.client.get(f"/game/{self.game_id}/state")
        original_state = state_response.json()

        # Save the game
        await self.client.post(
            f"/game/{self.game_id}/save",
            json={"session_name": "State Preservation Test"}
        )

        # Load the game
        load_response = await self.client.post(f"/game/{self.game_id}/load")
        loaded_session = load_response.json()["session"]

        # Verify key state elements are preserved
        self.assertEqual(
            loaded_session["location"],
            original_state["location"]
        )
        self.assertEqual(
            loaded_session["character"]["name"],
            original_state["character"]["name"]
        )
        # Turn count might increase by 1 due to the load operation
        self.assertGreaterEqual(
            loaded_session["turn_count"],
            original_state["turn_count"]
        )

    async def test_save_tracks_discoveries(self):
        """Test that saving creates discovery records for visited rooms."""
        # Execute movement commands to discover rooms
        await self.client.post(
            f"/game/{self.game_id}/command",
            json={"command": "north"}
        )

        # Save the game
        await self.client.post(
            f"/game/{self.game_id}/save",
            json={"session_name": "Discovery Test"}
        )

        # Load and verify discoveries are tracked
        load_response = await self.client.post(f"/game/{self.game_id}/load")
        loaded_session = load_response.json()["session"]

        # Should have discovered at least the starting room
        self.assertIn("discovered", loaded_session)
        self.assertIsInstance(loaded_session["discovered"], list)
        self.assertGreater(len(loaded_session["discovered"]), 0)

    async def test_update_existing_save(self):
        """Test that saving again updates the existing save."""
        # Save with initial name
        save1_response = await self.client.post(
            f"/game/{self.game_id}/save",
            json={"session_name": "Version 1"}
        )
        self.assertEqual(save1_response.status_code, 200)

        # Make more progress
        await self.client.post(
            f"/game/{self.game_id}/command",
            json={"command": "look around"}
        )

        # Save again with different name
        save2_response = await self.client.post(
            f"/game/{self.game_id}/save",
            json={"session_name": "Version 2"}
        )
        self.assertEqual(save2_response.status_code, 200)

        # List saves - should only have one entry for this game_id
        list_response = await self.client.get("/game/saves")
        list_data = list_response.json()

        matching_saves = [
            s for s in list_data["saves"]
            if s["game_id"] == self.game_id
        ]

        # Should be the updated save
        self.assertEqual(len(matching_saves), 1)
        self.assertEqual(matching_saves[0]["session_name"], "Version 2")


if __name__ == '__main__':
    unittest.main()
