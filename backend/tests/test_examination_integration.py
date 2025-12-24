"""Integration tests for examination and RAG content quality."""
import os
import unittest
import requests

# Use backend:8000 when running in Docker, localhost:8001 when running locally
BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8001')
TIMEOUT = 10


@unittest.skipUnless(os.getenv('RUN_INTEGRATION_TESTS'), 'Integration tests disabled')
class TestExamination(unittest.TestCase):
    """Test examination commands and RAG content quality."""

    def setUp(self):
        """Create a game session for each test."""
        response = requests.post(
            f"{BASE_URL}/game/start",
            json={"name": "ExamineTester", "character_class": "warrior"},
            timeout=TIMEOUT
        )
        self.game_id = response.json()["game_id"]

    def test_examine_room_feature(self):
        """Test examining a specific room feature (carved symbols)."""
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "examine ancient carved symbols"},
            timeout=TIMEOUT
        )
        
        data = response.json()
        description = data["response"]
        
        # Verify substantive content
        self.assertGreater(len(description), 100)
        # No bullet points
        self.assertNotIn("\n-", description)
        # No markdown headers
        self.assertNotIn("#", description)

    def test_examine_item_in_room(self):
        """Test examining an item focuses on that item, not others."""
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "examine leather pack"},
            timeout=TIMEOUT
        )
        
        data = response.json()
        description = data["response"].lower()
        
        # Should mention the pack
        self.assertIn("pack", description)
        # Should NOT be a long description mentioning rope AND torch AND pack
        # (indicating it returned a general room description)
        multiple_items = ("rope" in description and "torch" in description and "pack" in description)
        self.assertFalse(multiple_items,
                        "Examination should focus on specific item, not all items")

    def test_examine_nonexistent_thing(self):
        """Test examining something that doesn't exist."""
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "examine invisible clown"},
            timeout=TIMEOUT
        )
        
        data = response.json()
        description = data["response"].lower()
        
        # Should give "not found" type message
        self.assertTrue(
            "don't see" in description or "not" in description,
            "Should indicate item not found"
        )
        # Should NOT be generic AI response
        self.assertNotIn("typical invisible clown", description)

    def test_examine_thing_in_different_room(self):
        """Test that you can't examine items from other rooms."""
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "examine healing potion"},  # In Hidden Alcove
            timeout=TIMEOUT
        )
        
        data = response.json()
        # Should either not find it or give generic response
        # (not detailed potion description)
        self.assertLess(len(data["response"]), 200)

    def test_look_around(self):
        """Test general 'look around' command."""
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "look around"},
            timeout=TIMEOUT
        )
        
        data = response.json()
        description = data["response"]
        
        # Should get room description
        self.assertGreater(len(description), 50)
        # No markdown or bullets
        self.assertNotIn("#", description)
        self.assertNotIn("\n-", description)


@unittest.skipUnless(os.getenv('RUN_INTEGRATION_TESTS'), 'Integration tests disabled')
class TestContentQuality(unittest.TestCase):
    """Test that RAG content is properly filtered and formatted."""

    def setUp(self):
        """Create a game session for each test."""
        response = requests.post(
            f"{BASE_URL}/game/start",
            json={"name": "ContentTester", "character_class": "warrior"},
            timeout=TIMEOUT
        )
        self.game_id = response.json()["game_id"]

    def test_no_markdown_headers_in_responses(self):
        """Verify no markdown headers appear in any responses."""
        commands = [
            "look around",
            "go north",
            "examine walls",
            "inventory"
        ]
        
        for cmd in commands:
            response = requests.post(
                f"{BASE_URL}/game/{self.game_id}/command",
                json={"command": cmd},
                timeout=TIMEOUT
            )
            
            description = response.json()["response"]
            self.assertNotIn("# ", description,
                           f"Command '{cmd}' returned markdown header")
            self.assertNotIn("## ", description,
                           f"Command '{cmd}' returned markdown header")

    def test_no_bullet_points_in_descriptions(self):
        """Verify no bullet points from atmospheric sections appear."""
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "go north"},
            timeout=TIMEOUT
        )
        
        description = response.json()["response"]
        # Check for bullet points at start of lines
        lines = description.split('\n')
        for line in lines:
            self.assertFalse(line.strip().startswith('-'),
                           f"Found bullet point: {line}")

    def test_no_metadata_in_responses(self):
        """Verify metadata lines don't appear in responses."""
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "look around"},
            timeout=TIMEOUT
        )
        
        description = response.json()["response"]
        metadata_keywords = ["## Items:", "## Location:", "## Connections:", ":**"]
        
        for keyword in metadata_keywords:
            self.assertNotIn(keyword, description,
                           f"Found metadata keyword: {keyword}")

    def test_content_length_appropriate(self):
        """Verify content is neither too short nor too long."""
        response = requests.post(
            f"{BASE_URL}/game/{self.game_id}/command",
            json={"command": "go north"},
            timeout=TIMEOUT
        )
        
        description = response.json()["response"]
        # Should be substantive but not overwhelming
        self.assertGreater(len(description), 50, "Description too short")
        self.assertLess(len(description), 2000, "Description too long")


if __name__ == '__main__':
    unittest.main()
