"""Export helpers for splat point clouds (PLY + convenience writers).

Provides `SplatExporter.save_ply` to write a simple ASCII PLY file
from a list of splat-like objects (objects with `.center`, `.color`,
`coeff` or `.to_dict()` output). This is intentionally minimal and
suitable for importing into Godot or other engines as a point cloud.
"""
from __future__ import annotations

from typing import Iterable, Optional
import os

def _to_tuple_floats(val, length=3):
    if val is None:
        return (0.0,) * length
    try:
        return tuple(float(x) for x in val[:length])
    except Exception:
        return (0.0,) * length


class SplatExporter:
    @staticmethod
    def save_ply(path: str, splats: Iterable, mapping: Optional[Iterable[int]] = None, ascii: bool = True) -> None:
        """Write splats to a PLY point-cloud file.

        Fields written per-vertex (in this order):
          x y z r g b alpha coeff

        - `splats` can be objects with attributes (`center`, `color`, `coeff`)
          or objects that implement `to_dict()` with the same keys.
        - `mapping` is ignored by default but reserved for future use.
        """
        verts = []
        for s in splats:
            if hasattr(s, "to_dict"):
                d = s.to_dict()
                center = _to_tuple_floats(d.get("center"))
                color = _to_tuple_floats(d.get("color"))
                coeff = float(d.get("coeff", 1.0))
                alpha = float(d.get("alpha", 1.0))
            else:
                center = _to_tuple_floats(getattr(s, "center", None))
                color = _to_tuple_floats(getattr(s, "color", None))
                coeff = float(getattr(s, "coeff", 1.0))
                alpha = float(getattr(s, "alpha", 1.0))

            # convert color from 0..1 floats to 0..255 ints
            r = int(max(0, min(255, round(color[0] * 255))))
            g = int(max(0, min(255, round(color[1] * 255))))
            b = int(max(0, min(255, round(color[2] * 255))))

            verts.append((float(center[0]), float(center[1]), float(center[2]), r, g, b, float(alpha), float(coeff)))

        # ensure directory
        d = os.path.dirname(os.path.abspath(path)) or "."
        os.makedirs(d, exist_ok=True)

        mode = "w" if ascii else "wb"
        # Only ASCII supported currently; binary reserved for future
        with open(path, mode) as f:
            # Header
            f.write("ply\n")
            f.write("format ascii 1.0\n")
            f.write(f"element vertex {len(verts)}\n")
            f.write("property float x\n")
            f.write("property float y\n")
            f.write("property float z\n")
            f.write("property uchar red\n")
            f.write("property uchar green\n")
            f.write("property uchar blue\n")
            f.write("property float alpha\n")
            f.write("property float coeff\n")
            f.write("end_header\n")

            # Body
            for v in verts:
                x, y, z, r, g, b, a, c = v
                f.write(f"{x} {y} {z} {r} {g} {b} {a} {c}\n")
