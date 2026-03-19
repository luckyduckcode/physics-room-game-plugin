extends Node3D

@export var velocity := Vector3.ZERO
@export var mass := 1.0

func apply_force(fx: float, fy: float, fz: float) -> void:
    var f = Vector3(fx, fy, fz)
    velocity += f / (mass if mass != 0 else 1.0)

func _physics_process(delta: float) -> void:
    translation += velocity * delta
