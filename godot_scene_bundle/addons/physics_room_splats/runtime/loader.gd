extends Reference
class_name SplatLoader

const CHUNK_SIZE := 65535

var pts: Array = []
var cols: Array = []
var alphas: Array = []
var coeffs: Array = []

func load_ply(path: String) -> void:
    pts.clear()
    cols.clear()
    alphas.clear()
    coeffs.clear()

    var f = File.new()
    var err = f.open(path, File.READ)
    if err != OK:
        push_error("SplatLoader: failed to open %s" % path)
        return

    var in_header = true
    while not f.eof_reached():
        var line = f.get_line()
        if in_header:
            if line.strip_edges().to_lower() == "end_header":
                in_header = false
            continue
        if line.strip_edges() == "":
            continue
        var parts = line.strip_edges().split(" ")
        if parts.size() < 8:
            continue
        var x = float(parts[0])
        var y = float(parts[1])
        var z = float(parts[2])
        var r = int(parts[3]) / 255.0
        var g = int(parts[4]) / 255.0
        var b = int(parts[5]) / 255.0
        var a = float(parts[6])
        var coeff = float(parts[7])
        pts.append(Vector3(x, y, z))
        cols.append(Color(r, g, b, a))
        alphas.append(a)
        coeffs.append(coeff)

    f.close()

func selected_indices_nearest(camera: Camera3D, max_splats: int) -> Array:
    var count = pts.size()
    var idxs = []
    for i in range(count):
        idxs.append(i)
    if camera != null:
        var cam_pos = camera.global_transform.origin
        idxs.sort_custom(self, "_sort_by_distance", cam_pos)
    var use_n = min(max_splats, count)
    return idxs.slice(0, use_n)

func _sort_by_distance(a, b, cam_pos):
    var pa = pts[a]
    var pb = pts[b]
    var da = pa.distance_to(cam_pos)
    var db = pb.distance_to(cam_pos)
    return int(sign(da - db))

func build_multimesh_instances(owner: Node, indices: Array, point_size: float = 0.06, shader_path: String = "") -> Array:
    var instances: Array = []
    var i = 0
    while i < indices.size():
        var chunk = indices.slice(i, i + CHUNK_SIZE)
        var mm = MultiMesh.new()
        mm.transform_format = MultiMesh.TRANSFORM_3D
        mm.color_format = MultiMesh.COLOR_8BIT
        mm.instance_count = chunk.size()

        for j in range(chunk.size()):
            var idx = chunk[j]
            var t = Transform3D()
            t.origin = pts[idx]
            mm.set_instance_transform(j, t)
            mm.set_instance_color(j, cols[idx])

        var mmi = MultiMeshInstance3D.new()
        mmi.multimesh = mm

        var mat_res = null
        if shader_path != "":
            var sh = ResourceLoader.load(shader_path)
            if sh and sh is Shader:
                var sm = ShaderMaterial.new()
                sm.shader = sh
                mat_res = sm

        if mat_res == null:
            var mat = StandardMaterial3D.new()
            mat.flags_unshaded = true
            mat.point_size = point_size
            mat_res = mat

        mmi.material_override = mat_res
        owner.add_child(mmi)
        instances.append(mmi)
        i += CHUNK_SIZE

    return instances
