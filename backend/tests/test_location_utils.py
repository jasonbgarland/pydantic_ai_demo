"""Test location normalization utilities."""
import unittest
from app.utils.location_utils import (
    normalize_location_name,
    display_location_name,
    get_display_name,
    get_normalized_name,
    KNOWN_LOCATIONS
)


class TestLocationNormalization(unittest.TestCase):
    """Test location name normalization functions."""

    def test_normalize_location_name(self):
        """Test normalizing location names to snake_case."""
        self.assertEqual(normalize_location_name("Cave Entrance"), "cave_entrance")
        self.assertEqual(normalize_location_name("Yawning Chasm"), "yawning_chasm")
        self.assertEqual(normalize_location_name("cave_entrance"), "cave_entrance")
        self.assertEqual(normalize_location_name("HIDDEN ALCOVE"), "hidden_alcove")

    def test_display_location_name(self):
        """Test converting normalized names to display format."""
        self.assertEqual(display_location_name("cave_entrance"), "Cave Entrance")
        self.assertEqual(display_location_name("yawning_chasm"), "Yawning Chasm")
        self.assertEqual(display_location_name("Cave Entrance"), "Cave Entrance")

    def test_get_display_name(self):
        """Test getting canonical display names."""
        self.assertEqual(get_display_name("cave_entrance"), "Cave Entrance")
        self.assertEqual(get_display_name("Cave Entrance"), "Cave Entrance")
        self.assertEqual(get_display_name("yawning_chasm"), "Yawning Chasm")

    def test_get_normalized_name(self):
        """Test getting canonical normalized names."""
        self.assertEqual(get_normalized_name("Cave Entrance"), "cave_entrance")
        self.assertEqual(get_normalized_name("cave_entrance"), "cave_entrance")
        self.assertEqual(get_normalized_name("Yawning Chasm"), "yawning_chasm")

    def test_known_locations_complete(self):
        """Test that all known locations are mapped."""
        expected_locations = {
            'cave_entrance',
            'hidden_alcove',
            'yawning_chasm',
            'crystal_treasury',
            'collapsed_passage',
        }
        self.assertEqual(set(KNOWN_LOCATIONS.keys()), expected_locations)

    def test_roundtrip_conversion(self):
        """Test that normalize -> display -> normalize is idempotent."""
        original = "Cave Entrance"
        normalized = normalize_location_name(original)
        displayed = display_location_name(normalized)
        re_normalized = normalize_location_name(displayed)

        self.assertEqual(normalized, re_normalized)
        self.assertEqual(displayed, original)


if __name__ == '__main__':
    unittest.main()
