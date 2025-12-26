"""Integration tests for game flow and session management."""
import os
import unittest
import requests

# Use backend:8000 when running in Docker, localhost:8001 when running locally
BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8001')
TIMEOUT = 10


@unittest.skipUnless(os.getenv('RUN_INTEGRATION_TESTS'), 'Integration tests disabled')
class TestSessionManagement(unittest.TestCase):
    """Test session creation and management."""

    def test_create_character_and_start_game(self):
        """Test creating a character and starting a new game session."""
        # Create character
        response = requests.post(
            f"{BASE_URL}/game/start",
            json={
                "name": "TestHero",
                "character_class": "warrior"
            },
            timeout=TIMEOUT
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify response structure
        self.assertIn("game_id", data)
        self.assertIn("session", data)

        game_id = data["game_id"]
        session = data["session"]

        # Verify session data
        self.assertEqual(session["character"]["name"], "TestHero")
        self.assertEqual(session["character"]["character_class"], "warrior")
        self.assertEqual(session["location"], "cave_entrance")
        self.assertEqual(len(session["inventory"]), 0)
        self.assertEqual(session["turn_count"], 0)

        return game_id

    def test_session_persistence(self):
        """Test that session state persists across multiple commands."""
        # Start game
        game_id = self.test_create_character_and_start_game()

        # Execute multiple commands
        commands = ["look around", "take rope", "inventory"]

        for cmd in commands:
            response = requests.post(
                f"{BASE_URL}/game/{game_id}/command",
                json={"command": cmd},
                timeout=TIMEOUT
            )
            self.assertEqual(response.status_code, 200)

        # Verify final state
        final_response = requests.post(
            f"{BASE_URL}/game/{game_id}/command",
            json={"command": "inventory"},
            timeout=TIMEOUT
        )

        data = final_response.json()
        self.assertGreater(data["turn"], 0)
        self.assertIn("rope", data["session"]["inventory"])


@unittest.skipUnless(os.getenv('RUN_INTEGRATION_TESTS'), 'Integration tests disabled')
class TestMovement(unittest.TestCase):
    """Test movement between rooms."""

    def setUp(self):
        """Create a game session for each test."""
        response = requests.post(
            f"{BASE_URL}/game/start",
            json={"name": "SessionTester", "character_class": "warrior"},
            timeout=TIMEOUT
        )
        self.game_id = response.json()["game_id"]

    def test_valid_movement_north(self):
        """Test moving north from Cave Entrance to Hidden Alcove."""
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "go north"},
            timeout=TIMEOUT
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify movement success
        self.assertTrue(data["success"])
        self.assertEqual(data["session"]["location"], "hidden_alcove")

        # Verify room description quality
        description = data["response"]
        self.assertGreater(len(description), 50)
        self.assertNotIn("#", description)  # No markdown headers
        self.assertNotIn("\n-", description)  # No bullet points

    def test_invalid_direction(self):
        """Test moving in an invalid direction."""
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "go west"},
            timeout=TIMEOUT
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify movement failed
        self.assertFalse(data["success"])
        self.assertEqual(data["session"]["location"], "cave_entrance")

        # Verify error message indicates invalid direction
        self.assertIn("cannot", data["response"].lower())

    def test_bidirectional_movement(self):
        """Test moving north then back south."""
        # Move north
        response1 = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "go north"},
            timeout=TIMEOUT
        )
        self.assertEqual(response1.json()["session"]["location"], "hidden_alcove")

        # Move back south
        response2 = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "go south"},
            timeout=TIMEOUT
        )
        self.assertEqual(response2.json()["session"]["location"], "cave_entrance")


if __name__ == '__main__':
    unittest.main()
