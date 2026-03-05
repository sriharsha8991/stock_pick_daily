"""
Shared utility functions.
"""


def normalize(value: float, min_val: float, max_val: float) -> float:
    """Normalize *value* to the 0-1 range given *min_val* and *max_val*."""
    if max_val == min_val:
        return 0.5
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))
