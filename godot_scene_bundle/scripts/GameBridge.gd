extends Node3D

@export var splats_path: String = "user://splats.json"
@export var params_path: String = "user://game_params.json"
@export var events_path: String = "user://events.json"
@export var reload_interval: float = 0.5
@export var temp_step: float = 0.05

var _acc: float = 0.0
var _atomic_renderer: Node = null
var game_params := {"temperature": 0.1}
var _last_events_count: int = 0
var _score: int = 0

func _ready():
    # find an AtomicSplatRenderer child if present
    _atomic_renderer = get_node_or_null("AtomicSplatRenderer")
    if _atomic_renderer == null:
        _atomic_renderer = $AtomicSplatRenderer if has_node("AtomicSplatRenderer") else null
    # attempt initial load
    _reload_splats()
    _write_params()
    _update_score_label()

func _process(delta: float) -> void:
    _acc += delta
    if _acc >= reload_interval:
        _acc = 0.0
        _reload_splats()
        _check_events()

    # simple input-driven parameter tweak
    if Input.is_action_just_pressed("ui_up"):
        game_params["temperature"] = float(game_params.get("temperature", 0.1)) + temp_step
        _write_params()
    elif Input.is_action_just_pressed("ui_down"):
        game_params["temperature"] = float(game_params.get("temperature", 0.1)) - temp_step
        _write_params()

func _reload_splats() -> void:
    if _atomic_renderer == null:
        return
    var f = File.new()
    if f.file_exists(splats_path):
        var err = f.open(splats_path, File.READ)
        if err == OK:
            var txt = f.get_as_text()
            f.close()
            # call the helper on the renderer to set splats
            if _atomic_renderer.has_method("set_splats_from_json"):
                _atomic_renderer.set_splats_from_json(splats_path)

func _check_events() -> void:
    var f = File.new()
    if not f.file_exists(events_path):
        return
    var err = f.open(events_path, File.READ)
    if err != OK:
        return
    var txt = f.get_as_text()
    f.close()
    var data = parse_json(txt)
    if typeof(data) != TYPE_DICTIONARY:
        return
    var events = data.get("events", [])
    if typeof(events) != TYPE_ARRAY:
        return
    var n = events.size()
    # authoritative score from server (if provided)
    if data.has("score"):
        _score = int(data.get("score", _score))
        _update_score_label()
    if n > _last_events_count:
        # new events arrived; flash and update last count
        var new_count = n - _last_events_count
        _last_events_count = n
        _flash_anomaly()

func _update_score_label() -> void:
    var lbl = get_node_or_null("ScoreLabel")
    if lbl != null:
        lbl.text = str("Score: ", _score)

func _flash_anomaly() -> void:
    var rect = get_node_or_null("AnomalyFlash")
    if rect == null:
        return
    rect.modulate = Color(1, 0.4, 0.0, 0.0)
    rect.visible = true
    # animate a quick fade using a tween-like approach
    rect.create_timer(0.05).connect("timeout", Callable(self, "_hide_flash"))

func _hide_flash() -> void:
    var rect = get_node_or_null("AnomalyFlash")
    if rect:
        rect.visible = false

func _write_params() -> void:
    var f = File.new()
    var err = f.open(params_path, File.WRITE)
    if err != OK:
        return
    var txt = to_json(game_params)
    f.store_string(txt)
    f.close()
