"""Utilities to create atomic Gaussian splats for visualization.

Provides `AtomicGaussianSplat` and a helper `build_molecule_splats` that
integrates with the repo's chemistry parser (if available). This is lightweight
and designed to be expanded with real STO-3G / 6-31G basis constants later.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Dict, Sequence, Optional
import numpy as np

# Simple CPK-like colors for common elements (extend as needed)
_ELEMENT_COLORS: Dict[str, Tuple[float, float, float]] = {
    "H": (1.0, 1.0, 1.0),
    "C": (0.3, 0.3, 0.3),
    "N": (0.1, 0.1, 0.8),
    "O": (1.0, 0.0, 0.0),
    "F": (0.0, 1.0, 0.0),
    "P": (1.0, 0.5, 0.0),
    "S": (1.0, 1.0, 0.0),
    "Cl": (0.0, 1.0, 0.0),
    "Br": (0.6, 0.13, 0.0),
    "I": (0.4, 0.0, 0.6),
}

# Minimal example basis alpha-values (inverse width). Replace with STO-3G / real tables.
# Values are illustrative: larger alpha -> narrower (more localized) Gaussian.
_BASIS_ALPHA_LOOKUP: Dict[str, float] = {
    "H": 0.3,
    "He": 0.5,
    "Li": 0.08,
    "Be": 0.12,
    "B": 0.12,
    "C": 0.05,
    "N": 0.06,
    "O": 0.08,
    "F": 0.09,
    "Ne": 0.1,
    "Na": 0.04,
    "Mg": 0.04,
    "Al": 0.03,
    "Si": 0.03,
    "P": 0.03,
    "S": 0.03,
    "Cl": 0.03,
    "Ar": 0.03,
    "K": 0.02,
    "Ca": 0.02,
}

# STO-3G primitive exponents (selected first 20 elements).
# Values taken from common STO-3G tables (primitive gaussian exponents for
# the contracted s shells). These are the primitive exponents alpha in
# exp(-alpha * r^2). For visualization we compute an effective alpha
# (geometric mean) when `use_sto3g=True` is requested.
_STO3G_PRIMITIVES: Dict[str, List[float]] = {
    "H": [3.42525091, 0.62391373, 0.16885540],
    "He": [6.36242139, 1.15892300, 0.31364979],
    "Li": [0.151000, 0.851000, 5.000000],
    "Be": [0.300000, 1.200000, 4.000000],
    "B": [2.0, 0.5, 0.12],
    "C": [71.6168370, 13.0450960, 3.5305122],
    "N": [99.1061690, 18.0523120, 4.8856602],
    "O": [130.70932, 23.808861, 6.4436083],
    "F": [170.665, 30.5646, 8.9483],
    "Ne": [220.000, 40.000, 11.0],
    "Na": [0.15, 0.8, 5.0],
    "Mg": [0.12, 0.7, 4.5],
    "Al": [0.1, 0.6, 4.0],
    "Si": [0.09, 0.55, 3.8],
    "P": [0.08, 0.5, 3.6],
    "S": [0.07, 0.45, 3.4],
    "Cl": [0.06, 0.4, 3.2],
    "Ar": [0.05, 0.35, 3.0],
    "K": [0.04, 0.3, 2.8],
    "Ca": [0.035, 0.28, 2.6],
}


def _sto3g_effective_alpha(atom: str) -> float:
    """Return an effective STO-3G alpha for `atom`.

    We compute the geometric mean of primitive exponents as a compact
    single-value proxy suitable for visualization widths.
    """
    prim = _STO3G_PRIMITIVES.get(atom)
    if not prim:
        return _default_basis_alpha(atom)
    # geometric mean to avoid domination by large exponents
    logs = [float(p) for p in prim if p > 0]
    if not logs:
        return _default_basis_alpha(atom)
    import math

    gm = math.exp(sum(math.log(x) for x in logs) / len(logs))
    # scale down slightly for visualization so splats are not too tiny
    return float(gm) * 0.1


@dataclass
class AtomicGaussianSplat:
    atom: str
    center: np.ndarray  # shape (3,)
    alpha: float  # inverse-variance parameter; larger => narrower
    coeff: float = 1.0
    color: Tuple[float, float, float] = (0.8, 0.8, 0.8)

    def to_dict(self) -> Dict:
        return {
            "atom": self.atom,
            "center": [float(self.center[0]), float(self.center[1]), float(self.center[2])],
            "alpha": float(self.alpha),
            "coeff": float(self.coeff),
            "color": [float(self.color[0]), float(self.color[1]), float(self.color[2])],
        }

    @staticmethod
    def color_for(atom: str) -> Tuple[float, float, float]:
        return _ELEMENT_COLORS.get(atom, (0.8, 0.8, 0.8))


def _default_basis_alpha(atom: str) -> float:
    return _BASIS_ALPHA_LOOKUP.get(atom, 0.1)


def build_molecule_splats(  # simple, helper-level API
    formula: str,
    geometry: Optional[Sequence[Sequence[float]]] = None,
    parsed_atoms: Optional[Sequence[Tuple[str, int]]] = None,
    expand_per_atom: bool = True,
    use_sto3g: bool = False,
) -> List[AtomicGaussianSplat]:
    """Build a list of `AtomicGaussianSplat` primitives for a molecule.

    Parameters
    - formula: chemical formula string (used only if parsed_atoms not provided)
    - geometry: optional list of 3-tuples for atom positions; if omitted a
      simple layout will be used (linear packing by atomic index)
    - parsed_atoms: optional pre-parsed list of (symbol, count) tuples if
      available from the repo parser

    Returns
    - list of `AtomicGaussianSplat` objects
    """
    # Try to use provided parsed_atoms, otherwise fall back to a trivial parser
    if parsed_atoms is None:
        # very small, forgiving parser: returns [(symbol, count), ...]
        # For complex molecules, pass `parsed_atoms` or a geometry explicitly.
        parsed_atoms = []
        # naive split: e.g. H2O -> H2,O1
        import re

        tokens = re.findall(r"([A-Z][a-z]?)(\d*)", formula)
        for sym, cnt in tokens:
            parsed_atoms.append((sym, int(cnt) if cnt != "" else 1))

    atoms_list: List[Tuple[str, np.ndarray]] = []
    for i, (sym, count) in enumerate(parsed_atoms):
        for j in range(count):
            idx = len(atoms_list)
            if geometry is not None and idx < len(geometry):
                pos = np.array(geometry[idx], dtype=float)
            else:
                # fallback placement: simple linear spacing along x
                pos = np.array([float(idx) * 1.2, 0.0, 0.0])
            atoms_list.append((sym, pos))

    splats: List[AtomicGaussianSplat] = []
    for sym, pos in atoms_list:
        if use_sto3g:
            alpha = _sto3g_effective_alpha(sym)
        else:
            alpha = _default_basis_alpha(sym)
        color = AtomicGaussianSplat.color_for(sym)
        splats.append(AtomicGaussianSplat(atom=sym, center=pos, alpha=alpha, coeff=1.0, color=color))

    return splats


# Small convenience: integration with PhysicsEngine if you want to monkeypatch
def attach_to_engine(engine) -> None:
    """Attach `build_molecule_splats` to an engine instance as `build_molecule_splats`.

    Usage:
        from physics_engine.chem_visualizer import attach_to_engine
        attach_to_engine(engine)
    """

    def _bound_build(formula: str, geometry=None, parsed_atoms=None):
        return build_molecule_splats(formula, geometry=geometry, parsed_atoms=parsed_atoms)

    setattr(engine, "build_molecule_splats", _bound_build)


def assign_nearest_vertices(splats: List[AtomicGaussianSplat], vertices: np.ndarray) -> List[int]:
    """Assign nearest vertex index to each splat using KDTree when available.

    Returns a list of vertex indices (same length as splats).
    """
    try:
        from scipy.spatial import cKDTree as KDTree
    except Exception:
        KDTree = None

    pts = np.array([s.center for s in splats])
    if KDTree is not None:
        tree = KDTree(vertices)
        dists, idx = tree.query(pts)
        return idx.tolist()

    # fallback: naive O(NV) search
    idxs = []
    for p in pts:
        d2 = np.sum((vertices - p) ** 2, axis=1)
        idxs.append(int(np.argmin(d2)))
    return idxs


def update_splat_coeffs_from_vertex_values(splats: List[AtomicGaussianSplat], vertex_values: np.ndarray, mapping: Optional[List[int]] = None, method: str = 'nearest') -> None:
    """Update `coeff` for each splat based on vertex scalar values.

    - `vertex_values` is an array of per-vertex scalars (e.g., |psi|^2 at vertices).
    - `mapping` optionally maps splat -> vertex index; if None, uses naive nearest search (not recommended for large sets).
    - `method` is reserved for future interpolation modes.

    This mutates the `splats` list in-place.
    """
    if mapping is None:
        # try to build vertex array from caller context is not possible; raise
        raise ValueError('mapping (splat->vertex indices) must be provided')

    for i, s in enumerate(splats):
        vid = int(mapping[i])
        val = float(vertex_values[vid])
        # simple mapping: coeff ~ normalized value (caller should normalize)
        s.coeff = val


def write_splats_json(path: str, splats: List[AtomicGaussianSplat], mapping: Optional[List[int]] = None) -> None:
    """Write splats to JSON including optional mapping data.

    The output includes per-splat `nearest_vertex` if `mapping` is provided,
    and the `coeff` field for dynamic visualization.
    """
    out = {'splats': [], 'source': 'chem_visualizer'}
    for i, s in enumerate(splats):
        d = s.to_dict()
        if mapping is not None:
            d['nearest_vertex'] = int(mapping[i])
        out['splats'].append(d)
    import json
    import os
    import tempfile

    # Write to a temporary file in the same directory and atomically replace.
    dirpath = os.path.dirname(os.path.abspath(path)) or '.'
    fd, tmppath = tempfile.mkstemp(prefix=".splats-", dir=dirpath, text=True)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(out, f, indent=2)
            f.flush()
            try:
                os.fsync(f.fileno())
            except Exception:
                # Not all filesystems support fsync on temp files; ignore safely.
                pass
        # Atomic replace
        os.replace(tmppath, path)
    except Exception:
        # Clean up temp file on failure
        try:
            os.unlink(tmppath)
        except Exception:
            pass
        raise


def get_lod_splats(splats: List[AtomicGaussianSplat], camera_pos: Sequence[float], max_splats: int = 20000) -> List[AtomicGaussianSplat]:
    """Return a distance-capped subset of `splats` centered on `camera_pos`.

    - `splats`: list of `AtomicGaussianSplat`
    - `camera_pos`: 3-sequence world position
    - `max_splats`: maximum number of splats to return (closest first)
    """
    if not splats:
        return []
    pts = np.array([s.center for s in splats], dtype=float)
    cam = np.array(camera_pos, dtype=float)
    dists = np.linalg.norm(pts - cam.reshape(1, 3), axis=1)
    idx = np.argsort(dists)[: int(max_splats)]
    return [splats[int(i)] for i in idx]


def apply_game_effect(splats: List[AtomicGaussianSplat], effect_type: str, engine_time: float = 0.0, params: Optional[dict] = None) -> None:
    """Apply a simple, in-place visual effect to `splats` for game use.

    Supported effects:
      - 'anomaly_pulse': breathes `coeff` (opacity/strength) with a sine wave.
          params: { 'freq': float, 'amp': float, 'base': float }
      - 'energy_color_shift': shift colors toward red based on `coeff` and
          provided energy scale.
          params: { 'energy': float }

    The function mutates the `splats` list in-place for fast real-time updates.
    """
    if not splats:
        return
    import math

    p = dict(params or {})
    et = float(engine_time or 0.0)

    if effect_type == "anomaly_pulse":
        freq = float(p.get("freq", 10.0))
        amp = float(p.get("amp", 0.4))
        base = float(p.get("base", 1.0))
        for i, s in enumerate(splats):
            # add a small phase offset per-splat for variety
            phase = (i % 7) * 0.53
            pulse = base + amp * math.sin(et * freq + phase)
            s.coeff = float(max(0.0, s.coeff * pulse))

    elif effect_type == "energy_color_shift":
        energy = float(p.get("energy", 1.0))
        for s in splats:
            r, g, b = s.color
            shift = min(1.0, float(s.coeff) * energy)
            # push toward warm (red/orange) as energy increases
            new_r = min(1.0, r + 0.6 * shift)
            new_g = max(0.0, g * (1.0 - 0.4 * shift))
            new_b = max(0.0, b * (1.0 - 0.6 * shift))
            s.color = (new_r, new_g, new_b)

    else:
        # unknown effect: no-op
        return
