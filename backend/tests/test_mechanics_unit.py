"""
Unit tests for simplified game mechanics module.

Tests SimpleAbilitySystem and victory/defeat detection.
"""
import unittest
from app.mechanics import (
    SimpleAbilitySystem,
    GameStatus,
    DefeatReason,
    initialize_game_mechanics,
    check_victory_condition,
    check_defeat_conditions,
    update_game_status,
    get_victory_narrative,
    get_defeat_narrative
)


class TestSimpleAbilitySystem(unittest.TestCase):
    """Tests for SimpleAbilitySystem class."""

    def setUp(self):
        """Set up test session before each test."""
        self.session = {
            "character": {"character_class": "Rogue", "health": 100},
            "location": "dark_passage",
            "inventory": []
        }

    def test_parse_ability_dash(self):
        """Test parsing dash ability."""
        result = SimpleAbilitySystem.parse_ability_command("dash north", "Warrior")
        self.assertTrue(result["is_ability"])
        self.assertEqual(result["ability_name"], "dash")

    def test_parse_ability_illuminate(self):
        """Test parsing illuminate ability."""
        result = SimpleAbilitySystem.parse_ability_command("illuminate", "Wizard")
        self.assertTrue(result["is_ability"])
        self.assertEqual(result["ability_name"], "illuminate")

    def test_parse_ability_sneak(self):
        """Test parsing sneak ability."""
        result = SimpleAbilitySystem.parse_ability_command("sneak south", "Rogue")
        self.assertTrue(result["is_ability"])
        self.assertEqual(result["ability_name"], "sneak")

    def test_parse_ability_invalid(self):
        """Test parsing invalid ability returns not-is_ability."""
        result = SimpleAbilitySystem.parse_ability_command("invalid_ability", "Warrior")
        self.assertFalse(result["is_ability"])

    def test_use_dash_ability(self):
        """Test using dash ability."""
        result = SimpleAbilitySystem.use_ability("dash", "Warrior", self.session)
        self.assertIn("success", result)
        self.assertIn("narrative", result)

    def test_use_illuminate_ability(self):
        """Test using illuminate ability."""
        result = SimpleAbilitySystem.use_ability("illuminate", "Wizard", self.session)
        self.assertIn("success", result)
        self.assertIn("narrative", result)

    def test_use_sneak_ability(self):
        """Test using sneak ability."""
        result = SimpleAbilitySystem.use_ability("sneak", "Rogue", self.session)
        self.assertIn("success", result)
        self.assertIn("narrative", result)


class TestVictoryDefeatConditions(unittest.TestCase):
    """Tests for victory and defeat condition checking."""

    def setUp(self):
        """Set up test session before each test."""
        self.session = {
            "character": {"health": 100},
            "location": "crystal_chamber",
            "inventory": [],
            "game_status": GameStatus.IN_PROGRESS,
            "defeat_reason": None,
            "turn_count": 1
        }

    def test_initialize_game_mechanics(self):
        """Test game mechanics initialization."""
        session = {}
        initialize_game_mechanics(session)
        self.assertEqual(session["game_status"], GameStatus.IN_PROGRESS)
        self.assertIsNone(session["defeat_reason"])

    def test_check_victory_when_in_progress(self):
        """Test victory check returns False when game is in progress."""
        self.session["game_status"] = GameStatus.IN_PROGRESS
        victory = check_victory_condition(self.session)
        self.assertFalse(victory)

    def test_check_victory_when_victory_set(self):
        """Test victory check returns True when VICTORY status is set."""
        self.session["game_status"] = GameStatus.VICTORY
        victory = check_victory_condition(self.session)
        self.assertTrue(victory)

    def test_check_victory_when_defeat(self):
        """Test victory check returns False when game is in defeat state."""
        self.session["game_status"] = GameStatus.DEFEAT
        victory = check_victory_condition(self.session)
        self.assertFalse(victory)

    def test_check_defeat_health_zero(self):
        """Test defeat when health reaches zero."""
        self.session["character"]["health"] = 0
        defeat_reason = check_defeat_conditions(self.session)
        self.assertEqual(defeat_reason, DefeatReason.HEALTH_DEPLETED)

    def test_check_defeat_health_negative(self):
        """Test defeat when health is negative."""
        self.session["character"]["health"] = -10
        defeat_reason = check_defeat_conditions(self.session)
        self.assertEqual(defeat_reason, DefeatReason.HEALTH_DEPLETED)

    def test_no_defeat_healthy(self):
        """Test no defeat when healthy."""
        self.session["character"]["health"] = 50
        defeat_reason = check_defeat_conditions(self.session)
        self.assertIsNone(defeat_reason)

    def test_update_game_status_already_victory(self):
        """Test game status update when VICTORY already set."""
        self.session["game_status"] = GameStatus.VICTORY
        narrative = update_game_status(self.session)
        self.assertEqual(self.session["game_status"], GameStatus.VICTORY)
        self.assertIsNotNone(narrative)
        self.assertIn("victory", narrative.lower())

    def test_update_game_status_defeat(self):
        """Test game status update on defeat."""
        self.session["character"]["health"] = 0
        narrative = update_game_status(self.session)
        self.assertEqual(self.session["game_status"], GameStatus.DEFEAT)
        self.assertEqual(self.session["defeat_reason"], DefeatReason.HEALTH_DEPLETED)
        self.assertIsNotNone(narrative)

    def test_update_game_status_in_progress(self):
        """Test game status remains in progress."""
        self.session["character"]["health"] = 50
        self.session["location"] = "crystal_chamber"
        narrative = update_game_status(self.session)
        self.assertEqual(self.session["game_status"], GameStatus.IN_PROGRESS)
        self.assertEqual(narrative, "")

    def test_get_victory_narrative(self):
        """Test victory narrative generation."""
        narrative = get_victory_narrative()
        self.assertIsNotNone(narrative)
        self.assertIn("victory", narrative.lower())

    def test_get_defeat_narrative_health(self):
        """Test defeat narrative for health depletion."""
        narrative = get_defeat_narrative(DefeatReason.HEALTH_DEPLETED)
        self.assertIsNotNone(narrative)

    def test_get_defeat_narrative_none(self):
        """Test defeat narrative with no reason."""
        narrative = get_defeat_narrative(None)
        self.assertEqual(narrative, "")


if __name__ == '__main__':
    unittest.main()
