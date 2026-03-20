"""Sample a mesh surface and produce Gaussian splats JSON for Godot.

Requires `trimesh` (pip install trimesh[runtime]) and its dependencies.
Usage:
  python mesh_to_splats.py path/to/model.obj --count 200 --out splats_mesh.json

Output JSON format matches the existing splats JSON used by the Godot renderers
(e.g. 'splats': [{"center": [x,y,z], "alpha": a, "coeff":1.0, "color": [r,g,b]}])
"""
from __future__ import annotations
import argparse
import json
import numpy as np


def main():
    p = argparse.ArgumentParser()
    p.add_argument('mesh', help='Path to mesh file (obj, glb, gltf, stl, etc)')
    p.add_argument('--count', type=int, default=500, help='Number of sample points')
    p.add_argument('--alpha', type=float, default=0.15, help='Default alpha for splats')
    p.add_argument('--adaptive', action='store_true', help='Adapt alpha per-sample using local face area')
    p.add_argument('--clamp-min', type=float, default=0.2, help='Minimum alpha multiplier')
    p.add_argument('--clamp-max', type=float, default=5.0, help='Maximum alpha multiplier')
    p.add_argument('--curvature', action='store_true', help='Adapt alpha using a curvature proxy')
    p.add_argument('--map-to-vertices', action='store_true', help='Include nearest mesh vertex index for each splat')
    p.add_argument('--curvature-scale', type=float, default=1.0, help='Scale factor for curvature-based alpha')
    p.add_argument('--out', default='splats_mesh.json')
    p.add_argument('--color', default='0.8,0.8,0.8', help='Comma-separated r,g,b in 0..1')
    args = p.parse_args()

    try:
        import trimesh
    except Exception:
        print('Please install trimesh (pip install "trimesh[runtime]")')
        raise

    mesh = trimesh.load(args.mesh, force='mesh')
    if mesh.is_empty:
        raise SystemExit('Loaded mesh is empty')

    # sample points on the surface
    pts, face_idx = trimesh.sample.sample_surface(mesh, args.count)

    # approximate normals (optional) -- not used directly now
    try:
        _ = mesh.vertex_normals
    except Exception:
        pass

    # color parse
    color = [float(c) for c in args.color.split(',')][:3]

    splats = []
    # prepare face areas for adaptive scaling if requested
    face_areas = None
    if args.adaptive:
        try:
            face_areas = mesh.area_faces
            # avoid zero areas
            face_areas = np.maximum(face_areas, 1e-12)
            median_area = float(np.median(face_areas))
        except Exception:
            face_areas = None

    # if curvature mapping is requested, compute a simple curvature proxy per face
    face_curv = None
    if args.curvature:
        try:
            # compute per-face normals and per-vertex normals are available from trimesh
            vnorms = mesh.vertex_normals
            f_idx = mesh.faces
            # face vertex normal variance as a simple curvature proxy
            face_curv = np.zeros(len(mesh.faces))
            for fi, verts in enumerate(f_idx):
                vn = vnorms[verts]
                # curvature proxy: mean pairwise angular deviation of vertex normals
                # fallback: use norm of normal differences
                diffs = vn - vn.mean(axis=0)
                face_curv[fi] = np.linalg.norm(diffs)
        except Exception:
            face_curv = None

    for i, pnt in enumerate(pts):
        alpha = float(args.alpha)
        if args.adaptive and face_areas is not None:
            fi = int(face_idx[i]) if i < len(face_idx) else 0
            local_area = float(face_areas[fi])
            # scale alpha inversely with area: small area -> larger alpha (narrower splat)
            scale = median_area / local_area if local_area > 0 else 1.0
            # clamp scale to avoid extremes
            scale = max(args.clamp_min, min(args.clamp_max, scale))
            alpha = alpha * scale
        # curvature-based modulation: increase alpha where curvature high (sharper)
        if args.curvature and face_curv is not None:
            fi = int(face_idx[i]) if i < len(face_idx) else 0
            c = float(face_curv[fi])
            # map curvature to multiplier via exponential scaling
            km = np.exp(args.curvature_scale * c)
            km = max(args.clamp_min, min(args.clamp_max, km))
            alpha = alpha * km

        splat = {
            'atom': 'X',
            'center': [float(pnt[0]), float(pnt[1]), float(pnt[2])],
            'alpha': float(alpha),
            'coeff': 1.0,
            'color': [color[0], color[1], color[2]],
        }
        if args.map_to_vertices:
            # compute nearest mesh vertex index (naive search)
            try:
                v = mesh.vertices
                # compute squared distances
                d2 = np.sum((v - pnt) ** 2, axis=1)
                vid = int(np.argmin(d2))
                splat['nearest_vertex'] = int(vid)
            except Exception:
                splat['nearest_vertex'] = None
        splats.append(splat)

    out = {'splats': splats, 'source': f'mesh:{args.mesh}'}
    with open(args.out, 'w') as f:
        json.dump(out, f, indent=2)

    print(f'Wrote {len(splats)} splats to {args.out}')


if __name__ == '__main__':
    main()
