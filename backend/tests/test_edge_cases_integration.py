"""Integration tests for edge cases and error handling."""
import os
import unittest
import requests

# Use backend:8000 when running in Docker, localhost:8001 when running locally
BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8001')
TIMEOUT = 10


@unittest.skipUnless(os.getenv('RUN_INTEGRATION_TESTS'), 'Integration tests disabled')
class TestEdgeCases(unittest.TestCase):
    """Test edge cases and unusual inputs."""

    def setUp(self):
        """Create a game session for each test."""
        response = requests.post(
            f"{BASE_URL}/game/start",
            json={"name": "EdgeTester", "character_class": "warrior"},
            timeout=TIMEOUT
        )
        self.game_id = response.json()["game_id"]

    def test_empty_command(self):
        """Test submitting an empty command."""
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": ""},
            timeout=TIMEOUT
        )

        # Should handle gracefully
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # May succeed or fail, but should have a response
        self.assertIn("response", data)

    def test_whitespace_only_command(self):
        """Test command with only whitespace."""
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "   "},
            timeout=TIMEOUT
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("response", data)

    def test_very_long_command(self):
        """Test extremely long command."""
        long_command = "examine " + "x" * 1000
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": long_command},
            timeout=TIMEOUT
        )

        # Should handle without crashing
        self.assertEqual(response.status_code, 200)

    def test_special_characters_in_command(self):
        """Test commands with special characters."""
        special_chars = [
            "take $$$",
            "examine @@@",
            "go north!!!",
            "look & listen",
        ]

        for cmd in special_chars:
            response = requests.post(
                f"{BASE_URL}/game/{self.game_id}/command",
                json={"command": cmd},
                timeout=TIMEOUT
            )

            # Should not crash
            self.assertEqual(response.status_code, 200)
            self.assertIn("response", response.json())

    def test_case_insensitive_commands(self):
        """Test that commands work regardless of case."""
        commands = [
            "INVENTORY",
            "inventory",
            "InVeNtOrY",
        ]

        for cmd in commands:
            response = requests.post(
                f"{BASE_URL}/game/{self.game_id}/command",
                json={"command": cmd},
                timeout=TIMEOUT
            )

            data = response.json()
            # All should work
            self.assertIn("inventory", data.get("session", {}))

    def test_mixed_case_item_names(self):
        """Test picking up items with mixed case."""
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "take MAGICAL ROPE"},
            timeout=TIMEOUT
        )

        data = response.json()
        # Should work due to normalization
        self.assertTrue(data["success"])
        inventory = data.get("session", {}).get("inventory", [])
        self.assertIn("magical_rope", inventory)

    def test_extra_whitespace_in_commands(self):
        """Test commands with extra whitespace."""
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "take    magical     rope"},
            timeout=TIMEOUT
        )

        data = response.json()
        # Should work with normalization
        self.assertTrue(data["success"])

    def test_invalid_session_id(self):
        """Test using an invalid session ID."""
        response = requests.post(
            f"{BASE_URL}/game/invalid-session-id/command",
            json={"command": "look around"},
            timeout=TIMEOUT
        )

        # Should return error or handle gracefully
        # Don't crash the server
        self.assertIn(response.status_code, [200, 404, 400])

    def test_unicode_in_command(self):
        """Test commands with unicode characters."""
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "examine 🗡️ sword"},
            timeout=TIMEOUT
        )

        # Should handle without crashing
        self.assertEqual(response.status_code, 200)


@unittest.skipUnless(os.getenv('RUN_INTEGRATION_TESTS'), 'Integration tests disabled')
class TestConcurrency(unittest.TestCase):
    """Test concurrent requests and rapid commands."""

    def setUp(self):
        """Create a game session for each test."""
        response = requests.post(
            f"{BASE_URL}/game/start",
            json={"name": "ConcurrencyTester", "character_class": "warrior"},
            timeout=TIMEOUT
        )
        self.game_id = response.json()["game_id"]

    def test_rapid_successive_commands(self):
        """Test sending commands rapidly in succession."""
        commands = [
            "look around",
            "inventory",
            "examine walls",
            "take pack",
            "inventory",
        ]

        for cmd in commands:
            response = requests.post(
                f"{BASE_URL}/game/{self.game_id}/command",
                json={"command": cmd},
                timeout=TIMEOUT
            )

            # All should succeed
            self.assertEqual(response.status_code, 200)
            self.assertIn("response", response.json())


if __name__ == '__main__':
    unittest.main()
