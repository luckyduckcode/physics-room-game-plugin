using System;
using System.IO;
using System.Collections.Generic;
using UnityEngine;

// Simple component that reads an ASCII PLY with per-vertex: x y z r g b alpha coeff
// and populates a ParticleSystem with the points and colors.
[RequireComponent(typeof(ParticleSystem))]
public class SplatLoader : MonoBehaviour
{
    public string plyPath = ""; // full or relative path
    public int maxParticles = 20000;

    void Start()
    {
        if (string.IsNullOrEmpty(plyPath))
        {
            Debug.LogWarning("SplatLoader: plyPath not set");
            return;
        }
        try
        {
            var pts = ParsePly(plyPath);
            ApplyToParticleSystem(pts);
        }
        catch (Exception ex)
        {
            Debug.LogError("SplatLoader error: " + ex.Message);
        }
    }

    struct PPoint { public Vector3 pos; public Color col; public float coeff; }

    List<PPoint> ParsePly(string path)
    {
        var list = new List<PPoint>();
        using (var sr = new StreamReader(path))
        {
            string line;
            bool inHeader = true;
            while ((line = sr.ReadLine()) != null)
            {
                if (inHeader)
                {
                    if (line.Trim().ToLower() == "end_header") { inHeader = false; }
                    continue;
                }
                if (string.IsNullOrWhiteSpace(line)) continue;
                var parts = line.Trim().Split(new[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries);
                if (parts.Length < 8) continue;
                float x = float.Parse(parts[0]);
                float y = float.Parse(parts[1]);
                float z = float.Parse(parts[2]);
                int r = int.Parse(parts[3]);
                int g = int.Parse(parts[4]);
                int b = int.Parse(parts[5]);
                float a = float.Parse(parts[6]);
                float coeff = float.Parse(parts[7]);
                var p = new PPoint { pos = new Vector3(x, y, z), col = new Color(r / 255f, g / 255f, b / 255f, a), coeff = coeff };
                list.Add(p);
                if (list.Count >= maxParticles) break;
            }
        }
        return list;
    }

    void ApplyToParticleSystem(List<PPoint> pts)
    {
        var ps = GetComponent<ParticleSystem>();
        var main = ps.main;
        main.maxParticles = Math.Max(main.maxParticles, pts.Count);

        var particles = new ParticleSystem.Particle[pts.Count];
        for (int i = 0; i < pts.Count; ++i)
        {
            particles[i].position = pts[i].pos;
            particles[i].startColor = pts[i].col;
            particles[i].startSize = 0.05f;
            particles[i].remainingLifetime = 100000f;
            particles[i].startLifetime = 100000f;
        }
        ps.SetParticles(particles, particles.Length);
    }
}
