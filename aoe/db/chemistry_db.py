"""Placeholder for chemistry DB adapter(s).

Implement adapters for PubChem, Materials Project, NIST, or local caches.
"""
from typing import Dict, Any


class ChemistryDB:
    def __init__(self):
        pass

    def lookup(self, formula_or_name: str) -> Dict[str, Any]:
        """Return physical properties for a material name/formula."""
        # placeholder: return a small set of example properties
        return {"density": 1.0, "melting_point": 100.0}
