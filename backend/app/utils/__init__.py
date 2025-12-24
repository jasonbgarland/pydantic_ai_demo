"""Utils package for shared utility functions."""
from .name_utils import (
    normalize_location_name,
    display_location_name,
    get_display_name,
    get_normalized_name,
    KNOWN_LOCATIONS,
)

__all__ = [
    'normalize_location_name',
    'display_location_name',
    'get_display_name',
    'get_normalized_name',
    'KNOWN_LOCATIONS',
]
