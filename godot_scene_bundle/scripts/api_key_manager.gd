extends Node

const API_KEY_FILE := "user://api_key.cfg"

func save_api_key(key: String) -> bool:
    var f = File.new()
    var err = f.open(API_KEY_FILE, File.WRITE)
    if err != OK:
        push_error("Failed to write API key file")
        return false
    var payload = {"api_key": key, "created_at": OS.get_unix_time()}
    f.store_string(JSON.print(payload))
    f.close()
    return true

func load_api_key() -> String:
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

func delete_api_key() -> bool:
    var f = File.new()
    if not f.file_exists(API_KEY_FILE):
        return true
    var err = f.remove(API_KEY_FILE)
    if err != OK:
        push_error("Failed to delete API key file")
        return false
    return true
