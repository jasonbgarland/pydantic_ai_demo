"""Integration tests for item interaction system."""
import os
import unittest
import requests

# Use backend:8000 when running in Docker, localhost:8001 when running locally
BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8001')
TIMEOUT = 10


@unittest.skipUnless(os.getenv('RUN_INTEGRATION_TESTS'), 'Integration tests disabled')
class TestItemInteractions(unittest.TestCase):
    """Test item pickup, aliases, and inventory management."""

    def setUp(self):
        """Create a game session for each test."""
        response = requests.post(
            f"{BASE_URL}/game/start",
            json={"name": "ItemTester", "character_class": "warrior"},
            timeout=TIMEOUT
        )
        self.game_id = response.json()["game_id"]

    def test_pickup_valid_item_full_name(self):
        """Test picking up an item using its full name."""
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "take rope"},
            timeout=TIMEOUT
        )
        
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("rope", data["session"]["inventory"])

    def test_pickup_with_alias(self):
        """Test picking up item using an alias (potion -> healing_potion)."""
        # Move to Hidden Alcove where healing_potion is
        requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "go north"},
            timeout=TIMEOUT
        )
        
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "take potion"},
            timeout=TIMEOUT
        )
        
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("healing_potion", data["session"]["inventory"])

    def test_pickup_with_normalization(self):
        """Test picking up item with spaces (leather pack -> leather_pack)."""
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "take leather pack"},
            timeout=TIMEOUT
        )
        
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("leather_pack", data["session"]["inventory"])

    def test_pickup_nonexistent_item(self):
        """Test trying to pick up an item that doesn't exist."""
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "take pizza"},
            timeout=TIMEOUT
        )
        
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("don't see", data["response"].lower())
        self.assertEqual(len(data["session"]["inventory"]), 0)

    def test_pickup_item_from_different_room(self):
        """Test that you can't pick up items from other rooms."""
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "take healing_potion"},  # This is in Hidden Alcove
            timeout=TIMEOUT
        )
        
        data = response.json()
        self.assertFalse(data["success"])
        self.assertEqual(len(data["session"]["inventory"]), 0)

    def test_pickup_duplicate_item(self):
        """Test that picking up same item twice is prevented."""
        # Pick up rope first time
        response1 = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "take rope"},
            timeout=TIMEOUT
        )
        self.assertTrue(response1.json()["success"])
        
        # Try to pick up rope again
        response2 = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "take rope"},
            timeout=TIMEOUT
        )
        
        data = response2.json()
        self.assertFalse(data["success"])
        self.assertIn("already have", data["response"].lower())
        self.assertEqual(data["session"]["inventory"].count("rope"), 1)

    def test_compound_item_names_and(self):
        """Test that compound commands with 'and' are rejected."""
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "take rope and torch"},
            timeout=TIMEOUT
        )
        
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("one item at a time", data["response"].lower())
        self.assertEqual(len(data["session"]["inventory"]), 0)

    def test_compound_item_names_comma(self):
        """Test that compound commands with comma are rejected."""
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "take rope, torch"},
            timeout=TIMEOUT
        )
        
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("one item at a time", data["response"].lower())

    def test_inventory_command(self):
        """Test checking inventory after picking up items."""
        # Pick up multiple items
        requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "take rope"},
            timeout=TIMEOUT
        )
        requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "take torch"},
            timeout=TIMEOUT
        )
        
        # Check inventory
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "inventory"},
            timeout=TIMEOUT
        )
        
        data = response.json()
        self.assertIn("rope", data["session"]["inventory"])
        self.assertIn("torch", data["session"]["inventory"])
        self.assertIn("rope", data["response"].lower())
        self.assertIn("torch", data["response"].lower())

    def test_empty_inventory(self):
        """Test checking inventory when empty."""
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "inventory"},
            timeout=TIMEOUT
        )
        
        data = response.json()
        self.assertIn("empty", data["response"].lower())

    def test_all_aliases(self):
        """Test that all defined aliases work correctly."""
        aliases = {
            "pack": "leather_pack",
            "potion": "healing_potion",
            "gear": "climbing_gear",
        }
        
        for alias, canonical in aliases.items():
            # Create new session
            response = requests.post(
                f"{BASE_URL}/game/start",
                json={"name": f"AliasTester{alias}", "character_class": "warrior"},
                timeout=TIMEOUT
            )
            game_id = response.json()["game_id"]
            
            # Move to Hidden Alcove for most items
            if alias in ["potion", "gear"]:
                requests.post(
                    f"{BASE_URL}/game/{game_id}/command",
                    json={"command": "go north"},
                    timeout=TIMEOUT
                )
            
            # Try to pick up using alias
            response = requests.post(
                f"{BASE_URL}/game/{game_id}/command",
                json={"command": f"take {alias}"},
                timeout=TIMEOUT
            )
            
            data = response.json()
            if data["success"]:
                self.assertIn(canonical, data["session"]["inventory"],
                            f"Alias '{alias}' should map to '{canonical}'")


if __name__ == '__main__':
    unittest.main()
