extends Node

@export var entity_scene: PackedScene
var entities := {}
var next_id := 1

func add_entity(position := Vector2.ZERO, mass := 1.0) -> int:
    var ent
    if entity_scene:
        ent = entity_scene.instantiate()
        ent.position = position
        if ent.has_variable("mass"):
            ent.mass = mass
        add_child(ent)
    else:
        ent = Node2D.new()
        ent.position = position
        add_child(ent)
    var id = next_id
    entities[id] = ent
    next_id += 1
    return id

func apply_force(id: int, fx: float, fy: float) -> void:
    var ent = entities.get(id, null)
    if ent == null:
        return
    if ent.has_method("apply_force"):
        ent.apply_force(fx, fy)
    else:
        if ent.has_variable("vx"):
            ent.vx = ent.vx + fx / (ent.mass if ent.has_variable("mass") and ent.mass != 0 else 1.0)
        if ent.has_variable("vy"):
            ent.vy = ent.vy + fy / (ent.mass if ent.has_variable("mass") and ent.mass != 0 else 1.0)

func step(delta: float) -> Dictionary:
    var snap = {}
    for id in entities.keys():
        var e = entities[id]
        var vx = 0.0
        var vy = 0.0
        if e.has_variable("vx"):
            vx = e.vx
        if e.has_variable("vy"):
            vy = e.vy
        snap[id] = {"position": e.position, "vx": vx, "vy": vy}
    return snap
