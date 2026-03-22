"""
manifold.py — AOE Manifold System
==================================
Each player has a unique address in the ledger with a skill-gated number
of manifold slots. A manifold is a full genesis snapshot of an object that
can be restored or cloned from at any time.

Usage:
    registry = ManifoldRegistry("./data/manifolds")
    player   = registry.get_or_create_player("p_a3f9", skill_tier="journeyman")
    mid      = player.save_manifold(object_data)
    clone    = player.restore_manifold(mid)
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
import fcntl
import os
from typing import Optional as _Optional

from .ledger.ledger import ObjectLedger
from typing import Optional


# ---------------------------------------------------------------------------
# Skill tier → slot count
# ---------------------------------------------------------------------------

SKILL_TIERS: dict[str, int] = {
    "apprentice": 2,
    "journeyman": 5,
    "artisan":    10,
    "master":     20,
}


def slots_for_tier(tier: str) -> int:
    tier = tier.lower()
    if tier not in SKILL_TIERS:
        raise ValueError(f"Unknown skill tier '{tier}'. Valid: {list(SKILL_TIERS)}")
    return SKILL_TIERS[tier]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Composition:
    """Molecular / material composition breakdown."""
    components: dict[str, float]   # e.g. {"Fe": 98.5, "C": 1.5}

    def to_dict(self) -> dict:
        return {"components": self.components}

    @classmethod
    def from_dict(cls, d: dict) -> "Composition":
        return cls(components=d["components"])


@dataclass
class PhysicalProperties:
    density:             Optional[float] = None   # g/cm³
    hardness:            Optional[float] = None   # Vickers HV
    melting_point:       Optional[float] = None   # °C
    projected_durability: Optional[float] = None  # 0–100 score

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, d: dict) -> "PhysicalProperties":
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__})


@dataclass
class SplatData:
    """Visual representation hint for the Gaussian splat renderer."""
    color:   list[float]  = field(default_factory=lambda: [0.5, 0.5, 0.5])  # RGB 0–1
    opacity: float        = 1.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "SplatData":
        return cls(color=d.get("color", [0.5, 0.5, 0.5]), opacity=d.get("opacity", 1.0))


@dataclass
class Manifold:
    """
    A full genesis snapshot of an object.
    Immutable once written — the genesis_hash guarantees integrity.
    """
    manifold_id:   str
    description:   str                 # natural language, e.g. "tempered steel sword"
    composition:   Composition
    properties:    PhysicalProperties
    splat:         SplatData
    genesis_hash:  str                 # SHA-256 of the canonical payload
    created_at:    float               # unix timestamp

    # Optional back-reference to the ledger transaction that originated this object
    ledger_tx:     Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "manifold_id":  self.manifold_id,
            "description":  self.description,
            "composition":  self.composition.to_dict(),
            "properties":   self.properties.to_dict(),
            "splat":        self.splat.to_dict(),
            "genesis_hash": self.genesis_hash,
            "created_at":   self.created_at,
            "ledger_tx":    self.ledger_tx,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Manifold":
        return cls(
            manifold_id  = d["manifold_id"],
            description  = d["description"],
            composition  = Composition.from_dict(d["composition"]),
            properties   = PhysicalProperties.from_dict(d["properties"]),
            splat        = SplatData.from_dict(d["splat"]),
            genesis_hash = d["genesis_hash"],
            created_at   = d["created_at"],
            ledger_tx    = d.get("ledger_tx"),
        )

    def clone(self) -> "Manifold":
        """Return a new Manifold with a fresh ID, preserving all genesis data."""
        return Manifold(
            manifold_id  = _new_id("MF"),
            description  = self.description,
            composition  = Composition(components=dict(self.composition.components)),
            properties   = PhysicalProperties(**asdict(self.properties)),
            splat        = SplatData(color=list(self.splat.color), opacity=self.splat.opacity),
            genesis_hash = self.genesis_hash,   # same hash — same origin
            created_at   = time.time(),
            ledger_tx    = self.ledger_tx,
        )


# ---------------------------------------------------------------------------
# Player record
# ---------------------------------------------------------------------------

@dataclass
class PlayerRecord:
    """
    One JSON file per player, stored at:
        <registry_root>/<player_id>.json
    """
    player_id:   str
    skill_tier:  str
    manifolds:   dict[str, Manifold] = field(default_factory=dict)

    # ── slot accounting ────────────────────────────────────────────────────

    @property
    def max_slots(self) -> int:
        return slots_for_tier(self.skill_tier)

    @property
    def used_slots(self) -> int:
        return len(self.manifolds)

    @property
    def free_slots(self) -> int:
        return self.max_slots - self.used_slots

    # ── manifold operations ────────────────────────────────────────────────

    def save_manifold(
        self,
        description:    str,
        composition:    dict[str, float],
        properties:     dict,
        splat:          dict | None     = None,
        ledger_tx:      str | None      = None,
    ) -> str:
        """
        Snapshot an object as a manifold.
        Returns the new manifold_id, or raises if slots are full.
        """
        if self.free_slots <= 0:
            raise SlotLimitError(
                f"Player '{self.player_id}' ({self.skill_tier}) has no free slots "
                f"({self.used_slots}/{self.max_slots}). Advance skill tier to unlock more."
            )

        mid  = _new_id("MF")
        comp = Composition(components=composition)
        phys = PhysicalProperties.from_dict(properties)
        spl  = SplatData.from_dict(splat) if splat else SplatData()
        ghash = _genesis_hash(description, composition, properties)

        self.manifolds[mid] = Manifold(
            manifold_id  = mid,
            description  = description,
            composition  = comp,
            properties   = phys,
            splat        = spl,
            genesis_hash = ghash,
            created_at   = time.time(),
            ledger_tx    = ledger_tx,
        )
        return mid

    def restore_manifold(self, manifold_id: str) -> Manifold:
        """Return the manifold. Caller decides whether to use it as-is or clone it."""
        if manifold_id not in self.manifolds:
            raise KeyError(f"Manifold '{manifold_id}' not found for player '{self.player_id}'.")
        return self.manifolds[manifold_id]

    def clone_manifold(self, manifold_id: str) -> str:
        """
        Clone an existing manifold into a new slot.
        Useful for crafting variants from a master blueprint.
        """
        source = self.restore_manifold(manifold_id)
        if self.free_slots <= 0:
            raise SlotLimitError("No free slots available for clone.")
        clone = source.clone()
        self.manifolds[clone.manifold_id] = clone
        return clone.manifold_id

    def delete_manifold(self, manifold_id: str) -> None:
        """Free a slot by removing a manifold."""
        if manifold_id not in self.manifolds:
            raise KeyError(f"Manifold '{manifold_id}' not found.")
        del self.manifolds[manifold_id]

    def upgrade_tier(self, new_tier: str) -> None:
        """Advance the player's skill tier (never downgrade past current slot usage)."""
        new_slots = slots_for_tier(new_tier)
        if new_slots < self.used_slots:
            raise ValueError(
                f"Cannot downgrade to '{new_tier}' — player has {self.used_slots} manifolds "
                f"but that tier only allows {new_slots}."
            )
        self.skill_tier = new_tier

    # ── serialisation ──────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "player_id":  self.player_id,
            "skill_tier": self.skill_tier,
            "manifolds":  {mid: m.to_dict() for mid, m in self.manifolds.items()},
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PlayerRecord":
        record = cls(player_id=d["player_id"], skill_tier=d["skill_tier"])
        record.manifolds = {
            mid: Manifold.from_dict(mdata)
            for mid, mdata in d.get("manifolds", {}).items()
        }
        return record


# ---------------------------------------------------------------------------
# Registry  (manages all player files on disk)
# ---------------------------------------------------------------------------

class ManifoldRegistry:
    """
    Thin file manager.  One JSON file per player under `root_dir`.

        root_dir/
            p_a3f9.json
            p_b7c2.json
            ...
    """

    def __init__(self, root_dir: str | Path, ledger: _Optional[ObjectLedger] = None) -> None:
        self.root = Path(root_dir)
        self.root.mkdir(parents=True, exist_ok=True)
        self.ledger = ledger

    def _path(self, player_id: str) -> Path:
        return self.root / f"{player_id}.json"

    def get_or_create_player(
        self,
        player_id:  str,
        skill_tier: str = "apprentice",
    ) -> PlayerRecord:
        path = self._path(player_id)
        if path.exists():
            return PlayerRecord.from_dict(json.loads(path.read_text()))
        record = PlayerRecord(player_id=player_id, skill_tier=skill_tier)
        self._write(record)
        return record

    def save_player(self, record: PlayerRecord) -> None:
        # If a ledger is present, append ledger transactions for any manifolds
        # that don't yet have a `ledger_tx` and record the returned hash.
        if self.ledger is not None:
            for mid, manifold in record.manifolds.items():
                if not manifold.ledger_tx:
                    action = {
                        "action": "save_manifold",
                        "player_id": record.player_id,
                        "manifold_id": mid,
                        "manifold": manifold.to_dict(),
                        "timestamp": time.time(),
                    }
                    tx = self.ledger.append(action)
                    manifold.ledger_tx = tx

        self._write(record)

    def _write(self, record: PlayerRecord) -> None:
        path = self._path(record.player_id)
        data = json.dumps(record.to_dict(), indent=2)

        tmp_path = path.with_suffix(".tmp")
        # Write to a temp file and fsync to ensure durability
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())

            # Acquire an exclusive lock on the target file (create it if needed)
            target_fd = open(path, "a", encoding="utf-8")
            try:
                fcntl.flock(target_fd.fileno(), fcntl.LOCK_EX)
                # Atomic replace
                os.replace(tmp_path, path)
            finally:
                try:
                    fcntl.flock(target_fd.fileno(), fcntl.LOCK_UN)
                except Exception:
                    pass
                target_fd.close()
        finally:
            # Clean up leftover temp file if present
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except Exception:
                pass

    def list_players(self) -> list[str]:
        return [p.stem for p in self.root.glob("*.json")]


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class SlotLimitError(Exception):
    """Raised when a player tries to save more manifolds than their tier allows."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _genesis_hash(description: str, composition: dict, properties: dict) -> str:
    payload = json.dumps(
        {"description": description, "composition": composition, "properties": properties},
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Quick smoke test  (python manifold.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import tempfile, os

    with tempfile.TemporaryDirectory() as tmp:
        registry = ManifoldRegistry(tmp)

        # Create a journeyman player
        player = registry.get_or_create_player("p_demo", skill_tier="journeyman")
        print(f"Player: {player.player_id}  tier={player.skill_tier}  slots={player.used_slots}/{player.max_slots}")

        # Save a tempered steel sword
        mid = player.save_manifold(
            description  = "tempered steel sword",
            composition  = {"Fe": 98.5, "C": 1.5},
            properties   = {"density": 7.85, "hardness": 620.0, "melting_point": 1480.0, "projected_durability": 94.0},
            splat        = {"color": [0.6, 0.6, 0.65], "opacity": 0.95},
            ledger_tx    = "TX_004",
        )
        print(f"Saved manifold: {mid}")

        # Save an oak shield
        mid2 = player.save_manifold(
            description  = "oak shield",
            composition  = {"cellulose": 60.0, "lignin": 28.0, "minerals": 12.0},
            properties   = {"density": 0.75, "hardness": 3.0, "melting_point": 300.0, "projected_durability": 61.0},
            splat        = {"color": [0.55, 0.35, 0.15], "opacity": 1.0},
        )
        print(f"Saved manifold: {mid2}  slots now {player.used_slots}/{player.max_slots}")

        # Clone the sword
        clone_id = player.clone_manifold(mid)
        print(f"Cloned sword → {clone_id}")

        # Persist and reload
        registry.save_player(player)
        reloaded = registry.get_or_create_player("p_demo")
        print(f"Reloaded {len(reloaded.manifolds)} manifolds from disk")

        # Restore the sword
        sword = reloaded.restore_manifold(mid)
        print(f"Restored: '{sword.description}'  hash={sword.genesis_hash[:12]}...")

        # Show the JSON file
        print("\n--- player JSON ---")
        print(json.dumps(reloaded.to_dict(), indent=2))
