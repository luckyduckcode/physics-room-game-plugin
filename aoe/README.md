# Alchemical Object Engine (AOE)

This folder contains the reference implementation scaffolding for the
Alchemical Object Engine described in `aoe-architecture.txt`.

High-level layout:

- `aoe/engine` — core AOE resolver (LLM + chemistry DB integration)
- `aoe/db` — adapters and caches for chemistry data sources
- `aoe/ledger` — append-only object ledger and hashing utilities
- `aoe/sim` — physics sim and interaction engine
- `aoe/renderer` — gaussian splat renderer adapter
- `aoe/integrations` — Unity / Unreal / Godot plugin adapters
- `aoe/api` — developer-facing API surface (examples)
- `aoe/examples` — small workflows (forge steel, cooking demo)
- `aoe/tests` — unit/integration tests

See `architecture.md` for the full architecture text and design notes.
