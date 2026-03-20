"""Simple gameplay helpers: anomaly events and scoring for game integration.

This module provides a lightweight `AnomalyManager` that can be polled from
the game loop (or simulation loop) to deterministically trigger anomaly
events and update a simple score. Events are simple dicts and can be exported
to JSON for Godot or other clients to consume.
"""
from __future__ import annotations

import time
from typing import Dict, List, Optional

import numpy as np


class AnomalyManager:
    """Manage random anomaly events with deterministic seeding and scoring.

    Usage:
      mgr = AnomalyManager(chance_per_second=0.02, seed=42)
      evt = mgr.maybe_trigger(now)
      if evt:
          # handle event (visuals / scoring)
          mgr.award_points(100)
"""

    def __init__(self, chance_per_second: float = 0.02, seed: Optional[int] = None) -> None:
        self.chance_per_second = float(chance_per_second)
        self.rng = np.random.default_rng(seed)
        self.last_time = time.time()
        self.score = 0
        self.events: List[Dict] = []

    def maybe_trigger(self, now: Optional[float] = None) -> Optional[Dict]:
        """Check whether an anomaly triggers between `self.last_time` and `now`.

        Returns an event dict if triggered, otherwise None.
        """
        if now is None:
            now = time.time()
        dt = max(0.0, now - self.last_time)
        self.last_time = now
        if dt <= 0.0:
            return None

        # Poisson probability of at least one event in dt
        lam = self.chance_per_second * dt
        if lam <= 0:
            return None
        # draw from Poisson; we only care if >=1
        n = self.rng.poisson(lam)
        if n <= 0:
            return None

        intensity = float(self.rng.random())
        event = {
            "timestamp": now,
            "type": "anomaly",
            "count": int(n),
            "intensity": intensity,
        }
        self.events.append(event)
        return event

    def award_points(self, points: int) -> None:
        try:
            self.score += int(points)
        except Exception:
            pass

    def reset(self) -> None:
        self.score = 0
        self.events.clear()

    def export_events(self) -> List[Dict]:
        return list(self.events)
