"""Integration tests for game session management endpoints."""
import os
import unittest
import requests


@unittest.skipUnless(os.getenv('RUN_INTEGRATION_TESTS'), 'Integration tests disabled')
class TestSessionIntegration(unittest.TestCase):
    """Integration tests that make real HTTP calls to the running service."""

    def setUp(self):
        """Set up test fixtures."""
        # Use internal Docker network address when running inside container
        self.base_url = "http://backend:8000"  # Internal service name and port
        self.timeout = 10

    def test_full_session_workflow(self):
        """Test complete session workflow from creation to commands."""
        # Create a new game session
        start_response = requests.post(f"{self.base_url}/game/start",
                                     json={"name": "IntegrationTester", "character_class": "warrior"},
                                     timeout=self.timeout)
        self.assertEqual(start_response.status_code, 200)
        
        start_data = start_response.json()
        self.assertIn("game_id", start_data)
        self.assertIn("session", start_data)
        
        game_id = start_data["game_id"]
        session = start_data["session"]
        
        # Verify session structure
        self.assertEqual(session["game_id"], game_id)
        self.assertEqual(session["character"]["name"], "IntegrationTester")
        self.assertEqual(session["character"]["character_class"], "warrior")
        self.assertEqual(session["location"], "dungeon_entrance")
        self.assertEqual(session["turn_count"], 0)
        self.assertIsInstance(session["inventory"], list)
        self.assertIsInstance(session["discovered"], list)

        # Get initial state
        state_response = requests.get(f"{self.base_url}/game/{game_id}/state",
                                    timeout=self.timeout)
        self.assertEqual(state_response.status_code, 200)
        
        state_data = state_response.json()
        self.assertEqual(state_data["game_id"], game_id)
        self.assertEqual(state_data["turn_count"], 0)

        # Send a command
        cmd_response = requests.post(f"{self.base_url}/game/{game_id}/command",
                                   json={"command": "look", "parameters": {"direction": "around"}},
                                   timeout=self.timeout)
        self.assertEqual(cmd_response.status_code, 200)
        
        cmd_data = cmd_response.json()
        self.assertEqual(cmd_data["game_id"], game_id)
        self.assertEqual(cmd_data["turn"], 1)
        self.assertIn("response", cmd_data)
        
        # Verify session was updated
        session_after_cmd = cmd_data["session"]
        self.assertEqual(session_after_cmd["turn_count"], 1)
        self.assertIn("history", session_after_cmd)
        self.assertEqual(len(session_after_cmd["history"]), 1)
        
        history_entry = session_after_cmd["history"][0]
        self.assertEqual(history_entry["turn"], 1)
        self.assertEqual(history_entry["command"], "look")
        self.assertEqual(history_entry["params"]["direction"], "around")

        # Send another command to verify turn increments
        cmd2_response = requests.post(f"{self.base_url}/game/{game_id}/command",
                                    json={"command": "go", "parameters": {"direction": "north"}},
                                    timeout=self.timeout)
        self.assertEqual(cmd2_response.status_code, 200)
        
        cmd2_data = cmd2_response.json()
        self.assertEqual(cmd2_data["turn"], 2)
        
        # Verify final state
        final_state_response = requests.get(f"{self.base_url}/game/{game_id}/state",
                                          timeout=self.timeout)
        self.assertEqual(final_state_response.status_code, 200)
        
        final_state = final_state_response.json()
        self.assertEqual(final_state["turn_count"], 2)
        self.assertEqual(len(final_state["history"]), 2)

    def test_character_creation_and_classes(self):
        """Test character creation and class information endpoints."""
        # Get available classes
        classes_response = requests.get(f"{self.base_url}/character/classes", 
                                      timeout=self.timeout)
        self.assertEqual(classes_response.status_code, 200)
        
        classes_data = classes_response.json()
        self.assertIn("classes", classes_data)
        
        classes = classes_data["classes"]
        for class_key in ["warrior", "wizard", "rogue"]:
            self.assertIn(class_key, classes)
            class_info = classes[class_key]
            self.assertIn("name", class_info)
            self.assertIn("description", class_info)
            self.assertIn("stats", class_info)
            self.assertIn("strengths", class_info)
            
            # Verify stats structure
            stats = class_info["stats"]
            for stat in ["strength", "magic", "agility", "health", "stealth"]:
                self.assertIn(stat, stats)
                self.assertIsInstance(stats[stat], int)
                self.assertGreater(stats[stat], 0)

        # Test character creation
        for class_name in ["warrior", "wizard", "rogue"]:
            char_response = requests.post(f"{self.base_url}/character/create",
                                        json={"name": f"Test{class_name.capitalize()}", 
                                              "character_class": class_name},
                                        timeout=self.timeout)
            self.assertEqual(char_response.status_code, 200)
            
            char_data = char_response.json()
            self.assertIn("character", char_data)
            self.assertIn("message", char_data)
            
            character = char_data["character"]
            self.assertEqual(character["name"], f"Test{class_name.capitalize()}")
            self.assertEqual(character["character_class"], class_name)
            self.assertEqual(character["level"], 1)
            self.assertIn("stats", character)

    def test_error_handling(self):
        """Test error handling for invalid requests."""
        # Test invalid character class
        invalid_class_response = requests.post(f"{self.base_url}/character/create",
                                             json={"name": "InvalidTest", "character_class": "invalid"},
                                             timeout=self.timeout)
        self.assertEqual(invalid_class_response.status_code, 422)  # Validation error

        # Test nonexistent game session
        nonexistent_state_response = requests.get(f"{self.base_url}/game/nonexistent-game-123/state",
                                                 timeout=self.timeout)
        self.assertEqual(nonexistent_state_response.status_code, 200)
        
        error_data = nonexistent_state_response.json()
        self.assertEqual(error_data["error"], "session_not_found")

        # Test command on nonexistent session
        nonexistent_cmd_response = requests.post(f"{self.base_url}/game/nonexistent-game-123/command",
                                                json={"command": "look"},
                                                timeout=self.timeout)
        self.assertEqual(nonexistent_cmd_response.status_code, 200)
        
        cmd_error_data = nonexistent_cmd_response.json()
        self.assertEqual(cmd_error_data["error"], "session_not_found")

    def test_health_and_root_endpoints(self):
        """Test basic health and root endpoints."""
        # Test health endpoint
        health_response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
        self.assertEqual(health_response.status_code, 200)
        
        health_data = health_response.json()
        self.assertEqual(health_data["status"], "healthy")

        # Test root endpoint
        root_response = requests.get(f"{self.base_url}/", timeout=self.timeout)
        self.assertEqual(root_response.status_code, 200)
        
        root_data = root_response.json()
        self.assertIn("message", root_data)
        self.assertIn("status", root_data)
        self.assertIn("services", root_data)


if __name__ == "__main__":
    unittest.main()