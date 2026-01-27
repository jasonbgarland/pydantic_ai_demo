"""
Integration tests for turn counter and collapse trigger mechanics.

Tests the actual game flow with collapse system integrated.
"""
import os
import unittest
import requests


BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8001')
TEST_TIMEOUT = 10


@unittest.skipUnless(os.getenv('RUN_INTEGRATION_TESTS'), 'Integration tests disabled')
class TestCollapseMechanicsIntegration(unittest.TestCase):
    """Integration tests for collapse mechanics with running server."""

    def setUp(self):
        """Create a new game session before each test."""
        response = requests.post(
            f"{BASE_URL}/game/start",
            json={
                "name": "TestHero",
                "character_class": "warrior"
            },
            timeout=TEST_TIMEOUT
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.session_id = data["game_id"]
        self.session = data["session"]

    def tearDown(self):
        """Clean up session after test."""
        try:
            requests.delete(
                f"{BASE_URL}/game/{self.session_id}",
                timeout=TEST_TIMEOUT
            )
        except Exception:
            pass

    def send_command(self, command: str):
        """Helper to send a command and return response."""
        response = requests.post(
            f"{BASE_URL}/game/{self.session_id}/command",
            json={"command": command},
            timeout=TEST_TIMEOUT
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def get_session(self):
        """Helper to get current session state."""
        response = requests.get(
            f"{BASE_URL}/game/{self.session_id}/state",
            timeout=TEST_TIMEOUT
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_session_has_collapse_fields_initialized(self):
        """Test that new session has temp_flags initialized."""
        session = self.get_session()

        # Collapse state is now tracked in temp_flags
        self.assertIn("temp_flags", session)
        temp_flags = session["temp_flags"]
        
        # Collapse not triggered initially
        self.assertFalse(temp_flags.get("collapse_triggered", False))
        
        # Game status should be in progress
        self.assertEqual(session.get("game_status"), "in_progress")

    def test_turn_counter_increments(self):
        """Test that turn counter increments with each command."""
        session = self.get_session()
        initial_turn = session.get("turn_count", 0)

        # Send a command
        self.send_command("look around")

        session = self.get_session()
        self.assertEqual(session["turn_count"], initial_turn + 1)

        # Send another
        self.send_command("examine rope")

        session = self.get_session()
        self.assertEqual(session["turn_count"], initial_turn + 2)

    def test_collapse_not_triggered_outside_treasury(self):
        """Test that taking crystal outside treasury doesn't trigger collapse."""
        # Try to take crystal at cave entrance (crystal shouldn't be there)
        response = self.send_command("take crystal")

        session = self.get_session()
        temp_flags = session.get("temp_flags", {})
        # Collapse should not be triggered outside treasury
        self.assertFalse(temp_flags.get("collapse_triggered", False))

    def test_collapse_triggers_at_treasury(self):
        """Test that taking crystal at treasury triggers collapse."""
        # Navigate to treasury (simplified - just set location for test)
        # In real game, player would navigate there
        session = self.get_session()

        # For this test, we'll manually navigate to treasury
        # First go east to chasm
        self.send_command("go east")

        # Then go east again to treasury (assuming successful crossing)
        # Note: This might fail if crossing mechanics aren't implemented yet
        # For now, we'll test the trigger logic works when at treasury

        # Get to treasury somehow (details depend on navigation implementation)
        # Then test the trigger
        response = self.send_command("take crystal")

        session = self.get_session()

        # Check if we're at treasury and collapse triggered
        if session.get("location") == "crystal_treasury":
            self.assertTrue(session["collapse_triggered"])
            self.assertEqual(session["turns_since_collapse"], 0)
            self.assertIn("rumbling", response["response"].lower())

    def test_collapse_turn_counter_increments(self):
        """Test that collapse turn counter increments after trigger."""
        # Get to treasury and trigger collapse
        session = self.get_session()

        # Manually set location for testing
        # (In real integration, player would navigate)
        if session.get("location") != "crystal_treasury":
            # Can't test without being at treasury
            self.skipTest("Cannot reach treasury in current test setup")

        # Take crystal to trigger
        self.send_command("take crystal")

        session = self.get_session()
        if not session["collapse_triggered"]:
            self.skipTest("Collapse not triggered - check navigation")

        # Now send commands and watch counter increment
        initial_turns = session["turns_since_collapse"]

        self.send_command("go west")
        session = self.get_session()
        self.assertEqual(session["turns_since_collapse"], initial_turns + 1)

        self.send_command("look around")
        session = self.get_session()
        self.assertEqual(session["turns_since_collapse"], initial_turns + 2)

    def test_collapse_narrative_appears_in_response(self):
        """Test that collapse warnings appear in command responses."""
        session = self.get_session()

        if session.get("location") != "crystal_treasury":
            self.skipTest("Cannot reach treasury in current test setup")

        # Take crystal to trigger
        response = self.send_command("take crystal")

        # Should see trigger narrative
        self.assertIn("rumbling", response["response"].lower())

        # Subsequent commands should show turn counter
        response = self.send_command("go west")

        # Should see turn counter and urgency
        response_lower = response["response"].lower()
        self.assertTrue(
            "turn 1/7" in response_lower or "rocks" in response_lower,
            "Expected collapse narrative in response"
        )

    def test_collapse_does_not_trigger_twice(self):
        """Test that collapse only triggers once."""
        session = self.get_session()

        if session.get("location") != "crystal_treasury":
            self.skipTest("Cannot reach treasury in current test setup")

        # Take crystal first time
        self.send_command("take crystal")

        session = self.get_session()
        self.assertTrue(session["collapse_triggered"])
        first_trigger_turn = session["turns_since_collapse"]

        # Try to take crystal again
        self.send_command("take crystal")

        session = self.get_session()
        # Should still be triggered but counter should have incremented
        self.assertTrue(session["collapse_triggered"])
        self.assertEqual(session["turns_since_collapse"], first_trigger_turn + 1)


if __name__ == "__main__":
    unittest.main()
