extends EditorPlugin

var _btn

func _enter_tree():
    # Minimal plugin: add a toolbar button that prints a reload hint
    _btn = Button.new()
    _btn.text = "Reload Splats"
    _btn.connect("pressed", Callable(self, "_on_reload_pressed"))
    add_control_to_container(CONTAINER_SPATIAL_EDITOR_MENU, _btn)

func _exit_tree():
    if _btn:
        remove_control_from_container(CONTAINER_SPATIAL_EDITOR_MENU, _btn)
        _btn.queue_free()

func _on_reload_pressed():
    print("Physics Room Splats: reload requested (implement in project scene)")
