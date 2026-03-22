"""
aoe_resolver.py — Alchemical Object Engine Resolver
=====================================================
FastAPI service that sits between Godot and the physics engine.

Flow:
    POST /aoe/resolve {"description": "tempered steel sword", "player_id": "p_a3f9"}
        → LLM resolves composition   (Fe 98.5%, C 1.5%)
        → PubChem lookup per component → physical properties
        → Writes splats.json + events.json  (Godot's GameBridge polls these)
        → Optionally saves a manifold if player has a free slot + skill unlock

Run:
    pip install fastapi uvicorn httpx
    OPENROUTER_API_KEY=sk-or-... uvicorn aoe_resolver:app --port 8011 --reload

    Get a free key at: https://openrouter.ai

Endpoints:
    POST /aoe/resolve          — resolve an object description
    GET  /aoe/last             — return the last resolved object (debug)
    GET  /aoe/health           — health check
"""

from __future__ import annotations

import json
import math
import os
import random
import time
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Optional manifold integration (use `aoe.manifold` when available)
# ---------------------------------------------------------------------------
try:
    from aoe.manifold import ManifoldRegistry, SlotLimitError
    from aoe.ledger.ledger import ObjectLedger
    _MANIFOLD_AVAILABLE = True
except Exception:
    # Import errors are expected in minimal installs — resolver will still work
    _MANIFOLD_AVAILABLE = False

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
# Free models: meta-llama/llama-3.1-8b-instruct:free  google/gemma-3-12b-it:free  mistralai/mistral-7b-instruct:free
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")

# Where Godot's GameBridge looks for output files
OUTPUT_DIR = Path(
    os.environ.get(
        "AOE_OUTPUT_DIR",
        Path(__file__).parent / "physics engine" / "examples" / "examples_output",
    )
)

MANIFOLD_DIR = Path(os.environ.get("AOE_MANIFOLD_DIR", "./data/manifolds"))

# Number of splat points to generate per resolved object
SPLAT_COUNT = int(os.environ.get("AOE_SPLAT_COUNT", "256"))

app = FastAPI(title="AOE Resolver", version="0.1.0")

# In-memory cache of the last resolved object (for /aoe/last)
_last_resolved: dict = {}

# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class ResolveRequest(BaseModel):
    description: str                     # "tempered steel sword"
    player_id:   Optional[str] = None    # if set, attempt manifold save
    save_manifold: bool        = False   # player must explicitly request save


class ComponentProperties(BaseModel):
    name:        str
    formula:     Optional[str]  = None
    percent:     float                   # 0–100
    density:     Optional[float] = None  # g/cm³
    melting_pt:  Optional[float] = None  # °C
    hardness:    Optional[float] = None  # Vickers HV (estimated)
    color_rgb:   list[float]    = [0.5, 0.5, 0.5]


class ResolveResponse(BaseModel):
    description:          str
    components:           list[ComponentProperties]
    bulk_density:         float
    bulk_hardness:        float
    bulk_melting_pt:      float
    projected_durability: float
    dominant_color:       list[float]
    splat_file:           str
    events_file:          str
    manifold_id:          Optional[str] = None
    resolved_at:          float


# ---------------------------------------------------------------------------
# LLM — resolve composition
# ---------------------------------------------------------------------------

_COMPOSITION_PROMPT = """\
You are a materials chemistry assistant for a game engine.
Given an object description, return ONLY a JSON array of its primary components.
Each item must have:
  - "name": common material name (e.g. "iron", "cellulose", "silicon dioxide")
  - "formula": chemical formula if known (e.g. "Fe", "C6H10O5", "SiO2"), else null
  - "percent": approximate mass percent as a float (all percents must sum to 100)

Rules:
- Maximum 5 components.
- Use real chemistry. No invented materials.
- Percents must sum to exactly 100.
- Return ONLY the JSON array. No explanation, no markdown.

Object: {description}
"""

async def llm_resolve_composition(description: str) -> list[dict]:
    """
    Call an OpenRouter model to resolve an object description into chemical components.
    Falls back to mock data if no API key is set (handy for offline dev/testing).
    """
    if not OPENROUTER_API_KEY:
        return _mock_composition(description)

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization":  f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type":   "application/json",
                # OpenRouter recommends these for free-tier routing
                "HTTP-Referer":   "https://github.com/luckyduckcode/physics-room-game-plugin",
                "X-Title":        "AOE Resolver",
            },
            json={
                "model":      OPENROUTER_MODEL,
                "max_tokens": 512,
                "messages": [
                    {
                        "role":    "user",
                        "content": _COMPOSITION_PROMPT.format(description=description),
                    }
                ],
            },
        )

    if resp.status_code != 200:
        raise HTTPException(502, f"LLM error {resp.status_code}: {resp.text[:300]}")

    raw = resp.json()["choices"][0]["message"]["content"].strip()

    # Strip accidental markdown fences some models add
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        components = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(502, f"LLM returned non-JSON: {raw[:200]}") from exc

    # Normalise percents to exactly 100
    total = sum(c.get("percent", 0) for c in components) or 1
    for c in components:
        c["percent"] = round(c.get("percent", 0) / total * 100, 2)

    return components


def _mock_composition(description: str) -> list[dict]:
    """Deterministic fallback when no API key is set. Useful for local dev."""
    desc = description.lower()
    if any(w in desc for w in ("iron", "steel", "sword", "blade", "axe")):
        return [
            {"name": "iron",   "formula": "Fe",  "percent": 98.5},
            {"name": "carbon", "formula": "C",   "percent": 1.5},
        ]
    if any(w in desc for w in ("wood", "oak", "shield", "plank", "bow")):
        return [
            {"name": "cellulose", "formula": "C6H10O5", "percent": 60.0},
            {"name": "lignin",    "formula": None,       "percent": 28.0},
            {"name": "minerals",  "formula": None,       "percent": 12.0},
        ]
    if any(w in desc for w in ("stone", "rock", "granite", "flint")):
        return [
            {"name": "silicon dioxide", "formula": "SiO2",  "percent": 70.0},
            {"name": "alumina",         "formula": "Al2O3", "percent": 15.0},
            {"name": "iron oxide",      "formula": "Fe2O3", "percent": 15.0},
        ]
    if any(w in desc for w in ("gold", "ring", "coin", "crown")):
        return [{"name": "gold", "formula": "Au", "percent": 100.0}]
    if any(w in desc for w in ("glass", "bottle", "vial", "lens")):
        return [
            {"name": "silicon dioxide", "formula": "SiO2",  "percent": 72.0},
            {"name": "sodium oxide",    "formula": "Na2O",  "percent": 14.0},
            {"name": "calcium oxide",   "formula": "CaO",   "percent": 14.0},
        ]
    # Generic fallback
    return [
        {"name": "organic matter", "formula": None, "percent": 70.0},
        {"name": "minerals",       "formula": None, "percent": 30.0},
    ]


# ---------------------------------------------------------------------------
# PubChem — look up physical properties per component
# ---------------------------------------------------------------------------

# Material property reference table — used when PubChem doesn't have what we need.
# Values are (density g/cm³, melting_pt °C, hardness HV, color RGB 0-1)
_MATERIAL_PROPS: dict[str, tuple[float, float, float, list[float]]] = {
    "fe":       (7.87,  1538, 608,  [0.55, 0.55, 0.60]),
    "c":        (2.26,  3550, 1000, [0.15, 0.15, 0.15]),
    "au":       (19.32, 1064, 216,  [1.00, 0.84, 0.00]),
    "ag":       (10.49, 962,  251,  [0.80, 0.80, 0.85]),
    "cu":       (8.96,  1085, 369,  [0.72, 0.45, 0.20]),
    "sio2":     (2.65,  1713, 1100, [0.90, 0.92, 0.95]),
    "al2o3":    (3.99,  2072, 1800, [0.85, 0.85, 0.88]),
    "fe2o3":    (5.24,  1565, 500,  [0.70, 0.25, 0.10]),
    "c6h10o5":  (1.50,  260,  30,   [0.90, 0.87, 0.72]),  # cellulose
    "na2o":     (2.27,  1132, 200,  [0.95, 0.95, 0.90]),
    "cao":      (3.35,  2613, 700,  [0.95, 0.95, 0.92]),
}

async def pubchem_lookup(formula: Optional[str], name: str) -> dict:
    """
    Fetch physical properties from PubChem for a given formula or name.
    Falls back to the reference table, then to generic estimates.
    """
    key = (formula or "").lower().replace(" ", "")
    if key in _MATERIAL_PROPS:
        d, mp, hv, col = _MATERIAL_PROPS[key]
        return {"density": d, "melting_pt": mp, "hardness": hv, "color_rgb": col}

    # Try PubChem property API
    if formula:
        url = (
            f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/formula/"
            f"{formula}/property/MolecularWeight,ExactMass/JSON"
        )
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                r = await client.get(url)
            if r.status_code == 200:
                data = r.json()
                props = data.get("PropertyTable", {}).get("Properties", [{}])[0]
                mw = props.get("MolecularWeight", 100)
                # Rough heuristics from molecular weight when we lack direct data
                density    = max(0.5, min(20.0, float(mw) / 50))
                melting_pt = max(-200, min(3500, float(mw) * 8))
                hardness   = max(1, min(2000, float(mw) * 3))
                color      = _name_to_color(name)
                return {
                    "density":    round(density, 2),
                    "melting_pt": round(melting_pt, 1),
                    "hardness":   round(hardness, 1),
                    "color_rgb":  color,
                }
        except Exception:
            pass  # network error — fall through to generic

    # Generic fallback
    return {
        "density":    1.0,
        "melting_pt": 300.0,
        "hardness":   50.0,
        "color_rgb":  _name_to_color(name),
    }


def _name_to_color(name: str) -> list[float]:
    """Deterministic color from material name — avoids grey-everything."""
    name = name.lower()
    if any(w in name for w in ("iron", "steel", "metal")):  return [0.55, 0.55, 0.62]
    if any(w in name for w in ("gold", "aurum")):           return [1.00, 0.84, 0.00]
    if any(w in name for w in ("silver", "argentum")):      return [0.80, 0.80, 0.85]
    if any(w in name for w in ("copper")):                  return [0.72, 0.45, 0.20]
    if any(w in name for w in ("carbon", "coal", "char")):  return [0.12, 0.12, 0.12]
    if any(w in name for w in ("wood", "cellulose", "oak")): return [0.55, 0.35, 0.15]
    if any(w in name for w in ("glass", "silica", "quartz")): return [0.85, 0.95, 1.00]
    if any(w in name for w in ("rust", "oxide", "iron ox")): return [0.70, 0.25, 0.10]
    if any(w in name for w in ("stone", "rock", "granite")): return [0.60, 0.58, 0.55]
    if any(w in name for w in ("organic", "lignin")):       return [0.65, 0.50, 0.30]
    # Hash the name to a stable but arbitrary color
    h = hash(name) & 0xFFFFFF
    return [((h >> 16) & 0xFF) / 255, ((h >> 8) & 0xFF) / 255, (h & 0xFF) / 255]


# ---------------------------------------------------------------------------
# Bulk property derivation
# ---------------------------------------------------------------------------

def derive_bulk_properties(components: list[ComponentProperties]) -> dict:
    """
    Rule-of-mixtures weighted average across all components.
    Returns bulk density, hardness, melting point, dominant color,
    and a projected durability score (0–100).
    """
    total = sum(c.percent for c in components) or 1

    density    = sum((c.density    or 1.0)   * c.percent for c in components) / total
    hardness   = sum((c.hardness   or 50.0)  * c.percent for c in components) / total
    melting_pt = sum((c.melting_pt or 300.0) * c.percent for c in components) / total

    # Weighted dominant color
    r = sum(c.color_rgb[0] * c.percent for c in components) / total
    g = sum(c.color_rgb[1] * c.percent for c in components) / total
    b = sum(c.color_rgb[2] * c.percent for c in components) / total

    # Projected durability: normalised blend of hardness + melting point
    # 100 = indestructible (tungsten-like), 0 = tissue paper
    durability = min(100.0, (hardness / 20) * 0.6 + (melting_pt / 100) * 0.4)
    durability = round(max(1.0, durability), 1)

    return {
        "bulk_density":         round(density, 3),
        "bulk_hardness":        round(hardness, 1),
        "bulk_melting_pt":      round(melting_pt, 1),
        "dominant_color":       [round(r, 3), round(g, 3), round(b, 3)],
        "projected_durability": durability,
    }


# ---------------------------------------------------------------------------
# Splat generation
# ---------------------------------------------------------------------------

def generate_splats(
    color:     list[float],
    density:   float,
    hardness:  float,
    count:     int = SPLAT_COUNT,
) -> list[dict]:
    """
    Generate Gaussian splat points for the resolved material.
    Layout mimics the existing exporter format so GameBridge loads it unchanged.

    Each splat: { x, y, z, r, g, b, alpha, coeff }
    """
    splats = []
    rng = random.Random(hash(tuple(color)))  # deterministic per material

    # Denser materials pack splats tighter; harder materials have sharper coefficients
    spread = max(0.1, 2.0 / (density ** 0.3))
    coeff  = min(1.0, hardness / 1000)

    for _ in range(count):
        # Gaussian cluster around origin
        x = rng.gauss(0, spread)
        y = rng.gauss(0, spread)
        z = rng.gauss(0, spread)

        # Slight color variance per splat for visual richness
        r = max(0.0, min(1.0, color[0] + rng.gauss(0, 0.04)))
        g = max(0.0, min(1.0, color[1] + rng.gauss(0, 0.04)))
        b = max(0.0, min(1.0, color[2] + rng.gauss(0, 0.04)))

        # Alpha falls off with distance from centre
        dist   = math.sqrt(x*x + y*y + z*z)
        alpha  = max(0.05, min(1.0, 1.0 - dist / (spread * 3)))

        splats.append({
            "x": round(x, 4), "y": round(y, 4), "z": round(z, 4),
            "r": round(r, 4), "g": round(g, 4), "b": round(b, 4),
            "alpha": round(alpha, 4),
            "coeff": round(coeff + rng.gauss(0, 0.02), 4),
        })

    return splats


# ---------------------------------------------------------------------------
# File writers  (match GameBridge's expected format)
# ---------------------------------------------------------------------------

def write_splats_json(splats: list[dict], meta: dict, out_dir: Path) -> str:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {"meta": meta, "splats": splats}
    path = out_dir / "splats.json"
    path.write_text(json.dumps(payload, indent=2))
    return str(path)


def write_events_json(description: str, components: list[ComponentProperties],
                      bulk: dict, out_dir: Path) -> str:
    out_dir.mkdir(parents=True, exist_ok=True)
    events = [
        {
            "type":      "aoe.resolved",
            "timestamp": time.time(),
            "description": description,
            "composition": [
                {"name": c.name, "formula": c.formula, "percent": c.percent}
                for c in components
            ],
            "bulk_properties": bulk,
        }
    ]
    path = out_dir / "events.json"
    path.write_text(json.dumps(events, indent=2))
    return str(path)


# ---------------------------------------------------------------------------
# Main resolve endpoint
# ---------------------------------------------------------------------------

@app.post("/aoe/resolve", response_model=ResolveResponse)
async def resolve(req: ResolveRequest) -> ResolveResponse:
    description = req.description.strip()
    if not description:
        raise HTTPException(400, "description must not be empty")

    # 1. LLM → composition
    raw_components = await llm_resolve_composition(description)

    # 2. PubChem → per-component physical properties
    components: list[ComponentProperties] = []
    for rc in raw_components:
        props = await pubchem_lookup(rc.get("formula"), rc.get("name", ""))
        components.append(ComponentProperties(
            name       = rc.get("name", "unknown"),
            formula    = rc.get("formula"),
            percent    = rc.get("percent", 0),
            density    = props["density"],
            melting_pt = props["melting_pt"],
            hardness   = props["hardness"],
            color_rgb  = props["color_rgb"],
        ))

    # 3. Bulk property derivation
    bulk = derive_bulk_properties(components)

    # 4. Generate splats
    splats = generate_splats(
        color    = bulk["dominant_color"],
        density  = bulk["bulk_density"],
        hardness = bulk["bulk_hardness"],
    )

    # 5. Write output files for Godot
    meta = {
        "description":          description,
        "bulk_density":         bulk["bulk_density"],
        "bulk_hardness":        bulk["bulk_hardness"],
        "bulk_melting_pt":      bulk["bulk_melting_pt"],
        "projected_durability": bulk["projected_durability"],
        "dominant_color":       bulk["dominant_color"],
    }
    splat_path  = write_splats_json(splats, meta, OUTPUT_DIR)
    events_path = write_events_json(description, components, bulk, OUTPUT_DIR)

    # 6. Optional manifold save
    manifold_id: Optional[str] = None
    if req.save_manifold and req.player_id and _MANIFOLD_AVAILABLE:
        # Provide a ledger instance to the registry so ledger_tx gets populated
        ledger = ObjectLedger()
        registry = ManifoldRegistry(MANIFOLD_DIR, ledger=ledger)
        player   = registry.get_or_create_player(req.player_id)
        try:
            manifold_id = player.save_manifold(
                description  = description,
                composition  = {c.name: c.percent for c in components},
                properties   = {
                    "density":             bulk["bulk_density"],
                    "hardness":            bulk["bulk_hardness"],
                    "melting_point":       bulk["bulk_melting_pt"],
                    "projected_durability": bulk["projected_durability"],
                },
                splat = {
                    "color":   bulk["dominant_color"],
                    "opacity": 1.0,
                },
            )
            registry.save_player(player)
        except SlotLimitError as exc:
            # Don't fail the resolve — just skip the save and note it
            print(f"[AOE] Manifold save skipped: {exc}")

    result = ResolveResponse(
        description          = description,
        components           = components,
        bulk_density         = bulk["bulk_density"],
        bulk_hardness        = bulk["bulk_hardness"],
        bulk_melting_pt      = bulk["bulk_melting_pt"],
        projected_durability = bulk["projected_durability"],
        dominant_color       = bulk["dominant_color"],
        splat_file           = splat_path,
        events_file          = events_path,
        manifold_id          = manifold_id,
        resolved_at          = time.time(),
    )

    global _last_resolved
    _last_resolved = result.model_dump()

    return result


# ---------------------------------------------------------------------------
# Debug / health endpoints
# ---------------------------------------------------------------------------

@app.get("/aoe/last")
async def last_resolved() -> dict:
    if not _last_resolved:
        raise HTTPException(404, "No object resolved yet in this session.")
    return _last_resolved


@app.get("/aoe/health")
async def health() -> dict:
    return {
        "status":            "ok",
        "llm_key_set":        bool(OPENROUTER_API_KEY),
        "llm_model":          OPENROUTER_MODEL,
        "manifold_available": _MANIFOLD_AVAILABLE,
        "output_dir":        str(OUTPUT_DIR),
    }


# ---------------------------------------------------------------------------
# Dev runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("aoe_resolver:app", host="127.0.0.1", port=8011, reload=True)
