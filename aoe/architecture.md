ALCHEMICAL OBJECT ENGINE
=========================

Game environment architecture

---

SYSTEM ARCHITECTURE
-------------------

Five layers sit between the player and the rendered world. Each layer has a
single responsibility. The player never touches chemistry — they just act, and
the universe resolves the result.

LAYER 1 — PLAYER / VR INPUT

Hand tracking · grab · combine · heat · strike · pour

LAYER 2 — ALCHEMICAL OBJECT ENGINE (AOE)

LLM resolves composition · chemistry DB lookup · property derivation

LAYER 3 — SIMULATION SUBSYSTEMS

Physics sim · Object ledger · Interaction engine

LAYER 4 — GAUSSIAN SPLAT RENDERER

Molecular arrangement → splat distribution → visual output

LAYER 5 — GAME ENGINE HOST

Unity · Unreal · Godot — scene graph, audio, networking, UI

Details and example flows match `aoe-architecture.txt` in the repository root.
