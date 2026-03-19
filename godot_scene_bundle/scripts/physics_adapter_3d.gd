extends Node3D

@export var entity_scene: PackedScene
var entities := {}
var next_id := 1

func add_entity(position := Vector3.ZERO, mass := 1.0) -> int:
    var ent
    if entity_scene:
        ent = entity_scene.instantiate()
        ent.translation = position
        if ent.has_variable("mass"):
            ent.mass = mass
        add_child(ent)
    else:
        var rb := null
        if Engine.has_singleton("RigidBody3D") or true:
            rb = RigidBody3D.new()
            rb.translation = position
            if rb.has_variable("mass"):
                rb.mass = mass
            var mesh = MeshInstance3D.new()
            var sphere = SphereMesh.new()
            sphere.radius = 0.5
            mesh.mesh = sphere
            rb.add_child(mesh)
            add_child(rb)
            ent = rb
        else:
            ent = Node3D.new()
            ent.translation = position
            add_child(ent)
    var id = next_id
    entities[id] = ent
    next_id += 1
    return id

func apply_force(id: int, fx: float, fy: float, fz: float) -> void:
    var ent = entities.get(id, null)
    if ent == null:
        return
    if ent.has_method("apply_force"):
        ent.apply_force(fx, fy, fz)
        return
    if ent is RigidBody3D:
        if ent.has_method("apply_central_impulse"):
            ent.apply_central_impulse(Vector3(fx, fy, fz))
        elif ent.has_method("apply_impulse"):
            ent.apply_impulse(Vector3.ZERO, Vector3(fx, fy, fz))
        elif ent.has_method("add_force"):
            ent.add_force(Vector3(fx, fy, fz), Vector3.ZERO)
        else:
            if ent.has_variable("velocity"):
                ent.velocity = ent.velocity + Vector3(fx, fy, fz) / (ent.mass if ent.has_variable("mass") and ent.mass != 0 else 1.0)
        return
    if ent.has_variable("velocity"):
        ent.velocity = ent.velocity + Vector3(fx, fy, fz) / (ent.mass if ent.has_variable("mass") and ent.mass != 0 else 1.0)

func step(delta: float) -> Dictionary:
    var snap = {}
    for id in entities.keys():
        var e = entities[id]
        var vel = Vector3.ZERO
        if e.has_variable("velocity"):
            vel = e.velocity
        snap[id] = {"position": e.translation, "velocity": vel}
    return snap
