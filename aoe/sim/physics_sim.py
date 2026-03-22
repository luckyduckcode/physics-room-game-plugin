"""Physics simulation scaffold.

This module should derive physical behaviour (density, hardness, conductivity,
stress/failure) from `MaterialData` produced by the AOE.
"""
from typing import Any


class PhysicsSim:
    def __init__(self):
        pass

    def apply_properties(self, material: Any):
        """Convert `material` properties into simulation parameters."""
        # placeholder
        return {}
