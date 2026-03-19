This bundle contains the Godot scenes and scripts required to run the example experiment UI.

Structure:
- `project.godot` — minimal Godot project file (uses Godot 4 format).
- `scripts/` — GDScript files (API client, adapters, controllers, entities).
- `scenes/` — PackedScene `.tscn` files for UI and example experiments.

How to use:
1. Open Godot 4 and choose "Import" or open this folder as a project.
2. The main scene is set to `res://scenes/experiment_ui.tscn`.
3. You can edit scenes, run the project, and use the `scripts/api_key_manager.gd` to save an API key in `user://`.

Notes:
- This is a lightweight bundle meant for prototyping; it stores an API key to `user:///api_key.cfg` by default — for production, use OS keyrings or encrypted storage.
- The HTTP client script defaults to `http://127.0.0.1:8000/simulate` — change `server_url` as needed.
