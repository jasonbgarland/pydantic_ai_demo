"""Utility functions for normalizing location names between display format and storage format."""

def normalize_location_name(location: str) -> str:
    """
    Convert a human-readable location name to the storage format used in metadata.

    Examples:
        "Cave Entrance" -> "cave_entrance"
        "Yawning Chasm" -> "yawning_chasm"
        "cave_entrance" -> "cave_entrance" (already normalized)

    Args:
        location: Human-readable or already-normalized location name

    Returns:
        Normalized location name in snake_case
    """
    return location.lower().replace(' ', '_').replace('-', '_')


def display_location_name(location: str) -> str:
    """
    Convert a normalized location name to human-readable display format.

    Examples:
        "cave_entrance" -> "Cave Entrance"
        "yawning_chasm" -> "Yawning Chasm"
        "Cave Entrance" -> "Cave Entrance" (already display format)

    Args:
        location: Normalized or already-display-formatted location name

    Returns:
        Human-readable location name with Title Case
    """
    # If already in title case with spaces, return as-is
    if ' ' in location and location[0].isupper():
        return location

    # Convert snake_case to Title Case
    return location.replace('_', ' ').title()


# Mapping for known locations (for validation and auto-completion)
KNOWN_LOCATIONS = {
    'cave_entrance': 'Cave Entrance',
    'hidden_alcove': 'Hidden Alcove',
    'yawning_chasm': 'Yawning Chasm',
    'crystal_treasury': 'Crystal Treasury',
    'collapsed_passage': 'Collapsed Passage',
}


def get_display_name(location: str) -> str:
    """
    Get the canonical display name for a location.
    Uses the known locations map if available, otherwise converts to title case.

    Args:
        location: Location name in any format

    Returns:
        Canonical display name
    """
    normalized = normalize_location_name(location)
    return KNOWN_LOCATIONS.get(normalized, display_location_name(normalized))


def get_normalized_name(location: str) -> str:
    """
    Get the canonical normalized name for a location.

    Args:
        location: Location name in any format

    Returns:
        Canonical normalized name (snake_case)
    """
    return normalize_location_name(location)


# Item name normalization (reuse same logic as locations)
def normalize_item_name(item_name: str) -> str:
    """
    Convert a human-readable item name to the storage format.

    Examples:
        "climbing gear" -> "climbing_gear"
        "healing potion" -> "healing_potion"
        "climbing_gear" -> "climbing_gear" (already normalized)

    Args:
        item_name: Human-readable or already-normalized item name

    Returns:
        Normalized item name in snake_case
    """
    return item_name.lower().replace(' ', '_').replace('-', '_')


def display_item_name(item_name: str) -> str:
    """
    Convert a normalized item name to human-readable display format.

    Examples:
        "climbing_gear" -> "Climbing Gear"
        "healing_potion" -> "Healing Potion"

    Args:
        item_name: Normalized or already-display-formatted item name

    Returns:
        Human-readable item name with Title Case
    """
    # If already in title case with spaces, return as-is
    if ' ' in item_name and item_name[0].isupper():
        return item_name

    # Convert snake_case to Title Case
    return item_name.replace('_', ' ').title()
