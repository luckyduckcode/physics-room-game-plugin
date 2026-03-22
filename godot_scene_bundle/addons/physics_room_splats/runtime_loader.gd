extends Node
class_name RuntimeSplatLoader

@export var ply_path: String = "res://example_splats.ply"
@export var point_size: float = 0.06
@export var max_splats: int = 20000
@export var auto_update_lod: bool = true
@export var lod_update_interval: float = 0.5
@export var shader_path: String = "res://addons/physics_room_splats/shaders/gaussian_splat.shader"

var _loader: SplatLoader = SplatLoader.new()
var _multimesh_instances: Array = []
var _time_accum: float = 0.0

func _ready() -> void:
    if not ply_path:
        return
    _loader.load_ply(ply_path)
    if _loader.pts.size() == 0:
        return
    refresh_lod()

func _process(delta: float) -> void:
    if not auto_update_lod:
        return
    _time_accum += delta
    if _time_accum >= lod_update_interval:
        _time_accum = 0.0
        refresh_lod()

func refresh_lod() -> void:
    # clear previous multimesh instances
    for m in _multimesh_instances:
        if is_instance_valid(m):
            m.queue_free()
    _multimesh_instances.clear()

    var cam = get_viewport().get_camera_3d()
    var selected = []
    if cam != null:
        selected = _loader.selected_indices_nearest(cam, max_splats)
    else:
        selected = _loader.selected_indices_nearest(null, max_splats)

    var instances = _loader.build_multimesh_instances(self, selected, point_size, shader_path)
    for inst in instances:
        _multimesh_instances.append(inst)
