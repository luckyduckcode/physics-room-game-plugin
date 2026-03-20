# AtomicSplatMultimeshRenderer.gd
# Uses MultiMeshInstance3D for fast, per-instance splat rendering with per-instance color
extends Node3D

@export var splat_data := []

var mm_instance: MultiMeshInstance3D

func _ready():
    setup_multimesh()

func setup_multimesh():
    if mm_instance:
        mm_instance.queue_free()

    mm_instance = MultiMeshInstance3D.new()
    add_child(mm_instance)

    var quad = QuadMesh.new()
    quad.size = Vector2(1.0, 1.0)

    var mm = MultiMesh.new()
    mm.transform_format = MultiMesh.TRANSFORM_3D
    mm.color_format = MultiMesh.COLOR_FLOAT
    mm.custom_data_format = MultiMesh.CUSTOM_DATA_FLOAT
    mm.mesh = quad
    mm_instance.multimesh = mm

    # Create an unshaded shader material similar to previous shader but compatible with MultiMesh
    var mat = ShaderMaterial.new()
    var shader = Shader.new()
    shader.code = """
shader_type spatial;
render_mode unshaded, depth_draw_alpha_prepass, blend_mix;

uniform sampler2D albedo_texture : hint_albedo;

void fragment() {
    // Use UV to compute Gaussian falloff
    float dx = UV.x - 0.5;
    float dy = UV.y - 0.5;
    float dist2 = dx*dx + dy*dy;
    float a = exp(-dist2 * 12.0);
    vec3 col = COLOR.rgb; // per-instance color
    ALBEDO = col;
    ALPHA = a * COLOR.a;
}
"""
    mat.shader = shader
    mm_instance.material_override = mat

    _populate_multimesh()

func _populate_multimesh():
    var mm = mm_instance.multimesh
    var n = splat_data.size()
    mm.instance_count = n
    for i in range(n):
        var d = splat_data[i]
        var pos = d.get('center', [0,0,0])
        var alpha = float(d.get('alpha', 0.1))
        # scale splat by alpha (user can tune mapping); keep minimum size
        var scale = max(0.02, alpha * 2.0)
        var tr = Transform3D(Basis.IDENTITY.scaled(Vector3(scale, scale, scale)), Vector3(pos[0], pos[1], pos[2]))
        mm.set_instance_transform(i, tr)
        var col = d.get('color', [0.8,0.8,0.8])
        # Use `coeff` as per-splat opacity multiplier when present
        var coeff = float(d.get('coeff', 1.0))
        var a = clamp(coeff, 0.0, 4.0)
        mm.set_instance_color(i, Color(col[0], col[1], col[2], a))

func set_splats_from_json(path: String):
    var f = File.new()
    if f.open(path, File.READ) != OK:
        push_error("Could not open " + path)
        return
    var data = parse_json(f.get_as_text())
    if typeof(data) == TYPE_DICTIONARY and data.has("splats"):
        splat_data = data["splats"]
        _populate_multimesh()
