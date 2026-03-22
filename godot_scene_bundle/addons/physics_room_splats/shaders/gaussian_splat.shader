// Gaussian splat shader (Godot 4.x shader language)
// Designed for use with POINTS/point-sprite meshes or MultiMesh instances.
// This shader renders each point as a smooth Gaussian disk using POINT_COORD
// (the built-in per-fragment coordinate for point sprites).

shader_type spatial;
// Use additive blending for splat compositing and keep alpha prepass disabled
render_mode unshaded, cull_disabled, depth_draw_alpha_prepass, blend_add;

uniform vec4 splat_color : hint_color = vec4(1.0, 0.6, 0.2, 1.0);
uniform float intensity = 1.0; // multiplies alpha
uniform float falloff = 8.0; // higher => tighter Gaussian

// LOD: base point size in pixels and a distance scale factor
uniform float base_point_size : hint_range(0.1, 64.0) = 16.0;
uniform float lod_scale : hint_range(0.0, 1.0) = 0.02;
uniform float min_point_size : hint_range(0.1, 64.0) = 2.0;
uniform float max_point_size : hint_range(0.1, 256.0) = 64.0;

void vertex() {
    // compute distance from camera to the world-space vertex
    float dist = distance(WORLD_VERTEX, CAMERA_POSITION);
    // size falls off with distance; adjust with lod_scale
    float size = base_point_size / (1.0 + dist * lod_scale);
    size = clamp(size, min_point_size, max_point_size);
    POINT_SIZE = size;
}

void fragment() {
    vec2 pc = POINT_COORD;
    vec2 d = pc - vec2(0.5);
    float r2 = dot(d, d);
    float w = exp(-falloff * r2);

    // Additive blending: multiply color by weight and intensity
    ALBEDO = splat_color.rgb * (w * intensity);
    // Keep alpha for depth prepass but main compositing uses additive blend
    ALPHA = clamp(splat_color.a * w * intensity, 0.0, 1.0);
}
