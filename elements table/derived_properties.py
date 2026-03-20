from dataclasses import dataclass
from typing import Optional
from math import isnan

@dataclass
class DerivedProperties:
    melting_point_K: Optional[float] = None
    boiling_point_K: Optional[float] = None
    phase_span_C: Optional[float] = None
    fusion_enthalpy_kJ_per_mol: Optional[float] = None

    @staticmethod
    def from_element(element) -> 'DerivedProperties':
        # Melting/boiling point in Kelvin
        mpK = element.melting_point + 273.15 if element.melting_point is not None else None
        bpK = element.boiling_point + 273.15 if element.boiling_point is not None else None
        # Phase span (liquid range)
        span = None
        if element.melting_point is not None and element.boiling_point is not None:
            span = element.boiling_point - element.melting_point
        # Fusion enthalpy estimate (Trouton-like rule)
        fusion = None
        if mpK is not None:
            R = 8.314  # J/(mol·K)
            fusion = R * mpK * 2.5 / 1000  # kJ/mol
        return DerivedProperties(
            melting_point_K=mpK,
            boiling_point_K=bpK,
            phase_span_C=span,
            fusion_enthalpy_kJ_per_mol=fusion
        )
