extends Node

func _run_test():
    var loader = SplatLoader.new()
    var path = "res://addons/physics_room_splats/tests/test_loader.ply"
    loader.load_ply(path)
    var n = loader.pts.size()
    if n != 3:
        push_error("SplatLoader.load_ply() failed: expected 3 points, got %d" % n)
        return false
    print("SplatLoader.load_ply() OK — loaded 3 points")
    return true

func _ready():
    var ok = _run_test()
    if ok:
        print("TEST PASSED")
    else:
        print("TEST FAILED")
    # quit the running scene if invoked from editor/command-line
    if Engine.is_editor_hint():
        get_tree().quit()
