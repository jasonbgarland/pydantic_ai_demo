"""Integration tests for AI Intent Parser against running backend.

These tests validate that:
1. The AI intent parser correctly classifies natural language commands
2. The API endpoints properly await async parse_command calls
3. The end-to-end flow works with real OpenAI API calls

Run with: RUN_INTEGRATION_TESTS=1 python -m unittest tests.test_intent_parser_integration
Requires: Backend running on http://localhost:8001 with OPENAI_API_KEY set
"""
import os
import unittest
import requests
import time


@unittest.skipUnless(os.getenv('RUN_INTEGRATION_TESTS'), 'Integration tests disabled')
class TestIntentParserIntegration(unittest.TestCase):
    """Test AI intent parser with real API calls."""
    
    BASE_URL = os.getenv('TEST_API_URL', 'http://localhost:8001')
    TIMEOUT = 15  # AI calls can take a few seconds
    game_id = None
    
    @classmethod
    def setUpClass(cls):
        """Create a test character and game session."""
        # Start game (creates character and session)
        response = requests.post(
            f"{cls.BASE_URL}/game/start",
            json={"name": "AI Parser Tester", "character_class": "warrior"},
            timeout=10
        )
        assert response.status_code == 200, f"Game start failed: {response.text}"
        game_data = response.json()
        cls.game_id = game_data["game_id"]
        
        # Give backend a moment to initialize
        time.sleep(1)
    
    def _send_command(self, command: str) -> dict:
        """Send a command to the backend and return the response."""
        response = requests.post(
            f"{self.BASE_URL}/game/{self.game_id}/command",
            json={"command": command},
            timeout=self.TIMEOUT
        )
        self.assertEqual(response.status_code, 200, 
                        f"Command failed: {response.status_code} - {response.text}")
        return response.json()
    
    def test_movement_command_simple(self):
        """Test AI classifies simple movement: 'go north'"""
        result = self._send_command("go north")
        
        # Should recognize movement
        self.assertIn("north", result.get("response", "").lower(), 
                     f"Response should mention north: {result}")
    
    def test_movement_command_natural(self):
        """Test AI classifies natural language movement: 'walk to the east'"""
        result = self._send_command("walk to the east")
        
        # AI should understand "walk to the east" means movement east
        response = result.get("response", "").lower()
        self.assertTrue("east" in response or "direction" in narrative,
                       f"Response should handle eastern movement: {result}")
    
    def test_pickup_command_natural(self):
        """Test AI classifies natural pickup: 'grab the shiny crystal'"""
        result = self._send_command("grab the shiny crystal")
        
        # Should recognize item interaction
        response = result.get("response", "").lower()
        self.assertTrue(
            "crystal" in response or "pick" in response or "item" in narrative,
            f"Response should handle crystal pickup: {result}"
        )
    
    def test_inventory_command_variations(self):
        """Test AI understands inventory variations"""
        variations = [
            "inventory",
            "check my bag",
            "what do I have",
            "show my items"
        ]
        
        for command in variations:
            with self.subTest(command=command):
                result = self._send_command(command)
                response = result.get("response", "").lower()
                
                # Should respond about inventory
                self.assertTrue(
                    "inventory" in response or "carrying" in response or "items" in narrative,
                    f"Command '{command}' should trigger inventory check: {result}"
                )
    
    def test_examine_command_natural(self):
        """Test AI classifies examine commands: 'look at the ancient door'"""
        result = self._send_command("look at the ancient door")
        
        # Should recognize examination
        response = result.get("response", "").lower()
        self.assertTrue(
            "door" in response or "examine" in response or "look" in narrative,
            f"Response should handle door examination: {result}"
        )
    
    def test_ability_command(self):
        """Test AI classifies ability usage: 'use dash'"""
        result = self._send_command("use dash")
        
        # Should recognize ability (dash is a warrior ability)
        response = result.get("response", "").lower()
        self.assertTrue(
            "dash" in response or "ability" in response or "move" in narrative,
            f"Response should handle dash ability: {result}"
        )
    
    def test_unknown_command(self):
        """Test AI handles unclear commands gracefully"""
        result = self._send_command("xyzzy abracadabra")
        
        # Should indicate it doesn't understand
        response = result.get("response", "").lower()
        self.assertTrue(
            "don't understand" in response or "unclear" in response or "try" in narrative,
            f"Response should indicate confusion: {result}"
        )
    
    def test_complex_natural_language(self):
        """Test AI handles complex natural language: 'I want to carefully examine the mysterious crystal'"""
        result = self._send_command("I want to carefully examine the mysterious crystal")
        
        # AI should extract the core intent: examine something related to crystal
        response = result.get("response", "").lower()
        self.assertTrue(
            "crystal" in response or result.get("metadata", {}).get("examined") == "crystal",
            f"AI should extract examine intent from complex sentence: {result}"
        )
    
    def test_command_with_extra_words(self):
        """Test AI filters out filler words: 'can you please go north for me'"""
        result = self._send_command("can you please go north for me")
        
        # Should understand the core: go north
        response = result.get("response", "").lower()
        self.assertTrue(
            "north" in response,
            f"AI should extract 'go north' from polite sentence: {result}"
        )
    
    def test_response_structure(self):
        """Test that responses have expected structure"""
        result = self._send_command("go north")
        
        # Verify response structure
        self.assertIn("response", result, "Response should include narrative")
        self.assertIn("agent", result, "Response should include agent name")
        self.assertIn("success", result, "Response should include success flag")
        
        # Agent should be one of our agents
        self.assertIn(result["agent"], [
            "AdventureNarrator", 
            "RoomDescriptor", 
            "InventoryManager", 
            "EntityManager",
            "SimpleAbilitySystem"
        ])
    
    def test_concurrent_commands(self):
        """Test multiple commands in sequence (simulating player session)"""
        commands = [
            "look around",
            "check my inventory", 
            "go north",
            "examine the room"
        ]
        
        for command in commands:
            with self.subTest(command=command):
                result = self._send_command(command)
                self.assertIsNotNone(result.get("response"), 
                                    f"Each command should get a response: {command}")


@unittest.skipUnless(os.getenv('RUN_INTEGRATION_TESTS'), 'Integration tests disabled')
class TestIntentParserPerformance(unittest.TestCase):
    """Test AI intent parser performance."""
    
    BASE_URL = os.getenv('TEST_API_URL', 'http://localhost:8001')
    game_id = None
    
    @classmethod
    def setUpClass(cls):
        """Create a test character and game session."""
        # Start game (creates character and session)
        response = requests.post(
            f"{cls.BASE_URL}/game/start",
            json={"name": "Perf Tester", "character_class": "warrior"},
            timeout=10
        )
        assert response.status_code == 200, f"Game start failed: {response.text}"
        game_data = response.json()
        cls.game_id = game_data["game_id"]
    
    def test_response_time_acceptable(self):
        """Test that AI classification completes within reasonable time"""
        import time
        
        start = time.time()
        response = requests.post(
            f"{self.BASE_URL}/game/{self.game_id}/command",
            json={"command": "go north"},
            timeout=15
        )
        elapsed = time.time() - start
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 10.0, 
                       f"AI classification took {elapsed:.2f}s, should be under 10s")
        print(f"\n✓ AI classification completed in {elapsed:.2f}s")


if __name__ == '__main__':
    # Run with: python -m unittest tests.test_intent_parser_integration -v
    unittest.main()
