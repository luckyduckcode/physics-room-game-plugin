"""Gaussian splat renderer adapter scaffold.

This module should convert molecular arrangement and material state into a
lightweight representation usable by engine-specific renderers.
"""


class SplatRenderer:
    def __init__(self):
        pass

    def build_splat_data(self, material):
        """Return renderer-agnostic splat data for `material`."""
        return {}
