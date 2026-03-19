extends Node

@export var adapter: Node
@export var spawn_position := Vector3(0, 0, 0)
@export var spawn_mass := 1.0
@export var running := false

var entity_id := -1
var time_elapsed := 0.0
var log := []

func _ready() -> void:
    if adapter == null and has_node("PhysicsAdapter"):
        adapter = $PhysicsAdapter

func start_experiment() -> void:
    if adapter == null:
        push_error("Physics adapter not set on ExperimentController")
        return
    entity_id = adapter.add_entity(spawn_position, spawn_mass)
    running = true
    time_elapsed = 0.0
    log.clear()

func stop_experiment() -> void:
    running = false

func reset_experiment() -> void:
    for c in adapter.get_children():
        c.queue_free()
    adapter.entities.clear()
    adapter.next_id = 1
    entity_id = -1
    time_elapsed = 0.0
    log.clear()

func _physics_process(delta: float) -> void:
    if not running:
        return
    time_elapsed += delta
    if entity_id != -1:
        adapter.apply_force(entity_id, 0.0, -9.8 * spawn_mass, 0.0)
    var snap = adapter.step(delta)
    log.append({"t": time_elapsed, "state": snap.get(entity_id)})

func get_log() -> Array:
    return log
