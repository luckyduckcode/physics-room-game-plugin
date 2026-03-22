# AOE Developer API

Minimal surface for developer usage and game integrations.

Suggested functions / methods:

- `create_object(description: str) -> MaterialData` — natural language in, material data out
- `apply_action(action: str, subject: object, **kwargs) -> MaterialData` — heat/combine/strike
- `get_splat_data(material: MaterialData) -> dict` — renderer-agnostic visual data

See `aoe/engine/aoe_core.py` for a small scaffold showing `create_object`.
