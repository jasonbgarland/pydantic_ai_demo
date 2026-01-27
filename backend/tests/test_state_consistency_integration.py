"""Integration tests for game state consistency."""
import os
import unittest
import requests

# Use backend:8000 when running in Docker, localhost:8001 when running locally
BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8001')
TIMEOUT = 10


@unittest.skipUnless(os.getenv('RUN_INTEGRATION_TESTS'), 'Integration tests disabled')
class TestStateConsistency(unittest.TestCase):
    """Test that game state remains consistent across commands."""

    def setUp(self):
        """Create a game session for each test."""
        response = requests.post(
            f"{BASE_URL}/game/start",
            json={"name": "StateTester", "character_class": "warrior"},
            timeout=TIMEOUT
        )
        self.game_id = response.json()["game_id"]

    def test_item_disappears_from_room_after_pickup(self):
        """When an item is picked up, it should no longer be in the room."""
        # Pick up an item
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "take magical rope"},
            timeout=TIMEOUT
        )
        self.assertTrue(response.json()["success"])

        # Try to pick it up again
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "take magical rope"},
            timeout=TIMEOUT
        )

        data = response.json()
        # Should fail because it's not in the room anymore
        self.assertFalse(data["success"],
                        "Should not be able to pick up same item twice")
        self.assertIn("already", data["response"].lower())

    def test_inventory_persists_across_rooms(self):
        """Items in inventory should persist when moving between rooms."""
        # Pick up item
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "take magical rope"},
            timeout=TIMEOUT
        )
        self.assertTrue(response.json()["success"])

        # Move to another room
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "go north"},
            timeout=TIMEOUT
        )
        self.assertTrue(response.json()["success"])

        # Check inventory
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "inventory"},
            timeout=TIMEOUT
        )

        data = response.json()
        inventory = data.get("session", {}).get("inventory", [])
        self.assertIn("magical_rope", inventory,
                     "Item should persist in inventory across rooms")

    def test_location_updates_correctly(self):
        """Location in game state should update when moving."""
        # Get initial location
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "look around"},
            timeout=TIMEOUT
        )
        initial_location = response.json()["session"]["location"]
        self.assertEqual(initial_location, "cave_entrance")

        # Move north
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "go north"},
            timeout=TIMEOUT
        )
        new_location = response.json()["session"]["location"]

        self.assertNotEqual(new_location, initial_location)
        self.assertEqual(new_location, "hidden_alcove")

    def test_multiple_sequential_actions(self):
        """Test a sequence of actions maintains consistent state."""
        # Pick up magical rope from cave entrance
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "take magical rope"},
            timeout=TIMEOUT
        )
        self.assertTrue(response.json()["success"])

        # Move to hidden alcove (north from cave entrance)
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "go north"},
            timeout=TIMEOUT
        )
        self.assertTrue(response.json()["success"])

        # Pick up healing potion from hidden alcove
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "take healing potion"},
            timeout=TIMEOUT
        )
        self.assertTrue(response.json()["success"])

        # Check final state
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "inventory"},
            timeout=TIMEOUT
        )

        data = response.json()
        inventory = data.get("session", {}).get("inventory", [])
        location = data.get("session", {}).get("location")

        # Should have both items
        self.assertIn("magical_rope", inventory)
        self.assertIn("healing_potion", inventory)
        # Should be in new location
        self.assertEqual(location, "hidden_alcove")

    def test_picked_items_not_examinable_in_original_room(self):
        """Items picked up shouldn't be examinable in the room anymore."""
        # Pick up the magical rope
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "take magical rope"},
            timeout=TIMEOUT
        )
        self.assertTrue(response.json()["success"])

        # Try to examine it
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "examine magical rope"},
            timeout=TIMEOUT
        )

        # Should either say it's not there or give generic response
        description = response.json()["response"].lower()
        # Should NOT give detailed pack description
        self.assertTrue(
            len(description) < 200 or "inventory" in description,
            "Should not give detailed description of picked-up item"
        )


if __name__ == '__main__':
    unittest.main()
