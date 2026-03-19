extends Node2D

@export var vx := 0.0
@export var vy := 0.0
@export var mass := 1.0

func apply_force(fx: float, fy: float) -> void:
    vx += fx / (mass if mass != 0 else 1.0)
    vy += fy / (mass if mass != 0 else 1.0)

func _physics_process(delta: float) -> void:
    position.x += vx * delta
    position.y += vy * delta
