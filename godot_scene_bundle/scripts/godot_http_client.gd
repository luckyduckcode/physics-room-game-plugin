extends Node

# Bundled Godot HTTP client (copied from repo). Attach an HTTPRequest
# child named `HTTPRequest` or edit the script to use a different node path.

@export var server_url: String = "http://127.0.0.1:8000/simulate"
@export var max_retries: int = 3
@export var retry_delay: float = 1.0 # seconds

var _api_key: String = ""
const API_KEY_FILE := "user://api_key.cfg"

onready var http := null
var _attempts: int = 0
var _last_payload: PackedString = null

func _ready() -> void:
    http = get_node_or_null("HTTPRequest")
    if http == null:
        http = HTTPRequest.new()
        add_child(http)
    if not http.is_connected("request_completed", self, "_on_HTTPRequest_request_completed"):
        http.connect("request_completed", Callable(self, "_on_HTTPRequest_request_completed"))
    _api_key = _load_api_key()

func run_simulation(psi0_real: Array, psi0_imag: Array, times: Array, overrides: Dictionary=null) -> void:
    _attempts = 0
    var payload = {
        "psi0_real": psi0_real,
        "psi0_imag": psi0_imag,
        "times": times,
        "overrides": overrides,
        "simulate_with_logs": true
    }
    var json = JSON.print(payload)
    _last_payload = json
    _do_request(json)

func _do_request(json_payload: String) -> void:
    _attempts += 1
    var headers = ["Content-Type: application/json"]
    if _api_key != "":
        headers.append("X-API-Key: %s" % _api_key)
    var err = http.request_raw(server_url, headers, json_payload.to_utf8())
    if err != OK:
        push_error("Failed to start HTTPRequest (code=%s)" % err)
        _maybe_retry()

func _maybe_retry() -> void:
    if _attempts < max_retries:
        var t = get_tree().create_timer(retry_delay)
        t.timeout.connect(Callable(self, "_on_retry_timeout"))
    else:
        push_error("Max retries reached (%d)" % max_retries)

func _on_retry_timeout() -> void:
    _do_request(_last_payload)

func _on_HTTPRequest_request_completed(result, response_code, headers, body):
    if response_code >= 200 and response_code < 300:
        var s = body.get_string_from_utf8()
        var parsed = JSON.parse(s)
        if parsed.error == OK:
            var data = parsed.result
            emit_signal("simulation_success", data)
            print("Simulation finished; energies length:", data.get("energies", []).size())
        else:
            push_error("Failed to parse JSON from server")
            emit_signal("simulation_error", "parse_error")
    else:
        if response_code >= 500 and response_code < 600:
            push_warning("Server error %d; will retry if attempts remain" % response_code)
            _maybe_retry()
        else:
            var msg = "HTTP request failed: %s" % response_code
            push_error(msg)
            emit_signal("simulation_error", msg)

signal simulation_success(data)
signal simulation_error(message)

func _load_api_key() -> String:
    var f = File.new()
    if not f.file_exists(API_KEY_FILE):
        return ""
    var err = f.open(API_KEY_FILE, File.READ)
    if err != OK:
        push_error("Failed to open API key file")
        return ""
    var content = f.get_as_text()
    f.close()
    var parsed = JSON.parse(content)
    if parsed.error != OK:
        push_error("Failed to parse API key file")
        return ""
    var d = parsed.result
    return d.get("api_key", "")

func save_api_key(key: String) -> bool:
    var f = File.new()
    var err = f.open(API_KEY_FILE, File.WRITE)
    if err != OK:
        push_error("Failed to write API key file")
        return false
    var payload = {"api_key": key, "created_at": OS.get_unix_time()}
    f.store_string(JSON.print(payload))
    f.close()
    _api_key = key
    return true

func delete_api_key() -> bool:
    var f = File.new()
    if not f.file_exists(API_KEY_FILE):
        return true
    var err = f.remove(API_KEY_FILE)
    if err != OK:
        push_error("Failed to delete API key file")
        return false
    _api_key = ""
    return true
