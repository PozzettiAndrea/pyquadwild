"""
Generate visual demo of pyquadwild for GitHub Pages.

Shows QuadWild BiMDF quad-dominant remeshing with different parameters,
rendering before (triangle mesh) and after (quad mesh) comparisons.
"""

import os
import shutil
import time
import textwrap
import numpy as np

import pyvista as pv

pv.OFF_SCREEN = True

import pyquadwild

OUT_DIR = os.path.join(os.path.dirname(__file__), "_site")

# Dark theme
BG_COLOR = "#1a1a2e"
MESH_COLOR_IN = "#4fc3f7"
MESH_COLOR_OUT = "#81c784"
EDGE_COLOR = "#222244"
TEXT_COLOR = "#e0e0e0"


def pv_mesh_from_numpy_tris(verts, faces):
    """Create PyVista mesh from triangle arrays."""
    n = len(faces)
    pv_faces = np.column_stack([np.full(n, 3, dtype=np.int32), faces]).ravel()
    return pv.PolyData(verts, pv_faces)


def pv_mesh_from_numpy_quads(verts, faces):
    """Create PyVista mesh from quad arrays (handles -1 padding)."""
    pv_faces_list = []
    for f in faces:
        valid = f[f >= 0]
        pv_faces_list.append(len(valid))
        pv_faces_list.extend(valid)
    pv_faces = np.array(pv_faces_list, dtype=np.int32)
    return pv.PolyData(verts, pv_faces)


def render_mesh(mesh, filename, title, color=MESH_COLOR_IN,
                window_size=(800, 600)):
    pl = pv.Plotter(off_screen=True, window_size=window_size)
    pl.add_mesh(mesh, color=color, show_edges=True, edge_color=EDGE_COLOR,
                line_width=0.5, lighting=True, smooth_shading=True)
    pl.add_text(title, position="upper_left", font_size=12, color=TEXT_COLOR)
    pl.set_background(BG_COLOR)
    pl.camera_position = "iso"
    pl.screenshot(filename, transparent_background=False)
    pl.close()


def get_mesh():
    """Get Stanford bunny, fallback to icosphere."""
    try:
        bunny = pv.examples.download_bunny()
        verts = np.array(bunny.points, dtype=np.float64)
        faces = np.array(bunny.faces.reshape(-1, 4)[:, 1:], dtype=np.int32)
        return verts, faces, "bunny.stl"
    except Exception:
        sphere = pv.Icosphere(nsub=4, radius=1.0)
        verts = np.array(sphere.points, dtype=np.float64)
        faces = np.array(sphere.faces.reshape(-1, 4)[:, 1:], dtype=np.int32)
        return verts, faces, "sphere.stl"


def run_demo(name, func, verts_in, faces_in, code, after_label="Output"):
    """Run pyquadwild, render before/after, return demo dict."""
    t0 = time.perf_counter()
    verts_out, faces_out = func(verts_in, faces_in)
    elapsed = time.perf_counter() - t0

    mesh_in = pv_mesh_from_numpy_tris(verts_in, faces_in)
    mesh_out = pv_mesh_from_numpy_quads(verts_out, faces_out)

    prefix = os.path.join(OUT_DIR, name)
    render_mesh(mesh_in, f"{prefix}_before.png",
                f"Input: {len(verts_in):,} verts, {len(faces_in):,} tris")
    render_mesh(mesh_out, f"{prefix}_after.png",
                f"{after_label}: {len(verts_out):,} verts, {len(faces_out):,} quads  ({elapsed:.1f}s)",
                color=MESH_COLOR_OUT)

    return {
        "name": name,
        "verts_in": len(verts_in),
        "faces_in": len(faces_in),
        "verts_out": len(verts_out),
        "faces_out": len(faces_out),
        "elapsed": elapsed,
        "code": code,
        "after_label": after_label,
    }


def html_escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def generate_html(sections):
    all_sections_html = ""
    for section in sections:
        all_sections_html += f"""
    <h2 class="section-title">{section['title']}</h2>
    <p class="section-sub">{section['subtitle']}</p>
"""
        for d in section["demos"]:
            code_html = html_escape(d["code"])
            label = d.get("after_label", "Output")
            all_sections_html += f"""
    <section class="demo">
      <div class="demo-grid">
        <div class="demo-code">
          <pre><code>{code_html}</code></pre>
          <p class="timing">{d['elapsed']:.1f}s &mdash; {d['verts_in']:,} &rarr; {d['verts_out']:,} verts, {d['faces_in']:,} tris &rarr; {d['faces_out']:,} quads</p>
        </div>
        <div class="demo-images">
          <div class="comparison">
            <div class="panel">
              <img src="{d['name']}_before.png" alt="Before">
              <span class="label">Input (tris)</span>
            </div>
            <div class="panel">
              <img src="{d['name']}_after.png" alt="After">
              <span class="label">{label}</span>
            </div>
          </div>
        </div>
      </div>
    </section>
"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>pyquadwild — Quad-Dominant Remeshing</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #0d1117;
      color: #c9d1d9;
      padding: 2rem;
      max-width: 1400px;
      margin: 0 auto;
    }}
    a {{ color: #58a6ff; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    header {{
      text-align: center;
      margin-bottom: 2.5rem;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid #21262d;
    }}
    header h1 {{ font-size: 2.2rem; margin-bottom: 0.3rem; color: #f0f6fc; }}
    header .sub {{ color: #8b949e; font-size: 1.1rem; margin-bottom: 1rem; }}
    .install {{
      background: #161b22;
      color: #aed581;
      padding: 0.8rem 1.5rem;
      border-radius: 6px;
      border: 1px solid #21262d;
      font-family: "SF Mono", "Fira Code", monospace;
      font-size: 0.95rem;
      display: inline-block;
      margin: 0.8rem 0;
    }}
    .links {{ margin-top: 0.8rem; color: #8b949e; }}
    .section-title {{
      font-size: 1.5rem;
      color: #f0f6fc;
      margin: 2.5rem 0 0.3rem 0;
      padding-top: 1.5rem;
      border-top: 1px solid #21262d;
    }}
    .section-sub {{
      color: #8b949e;
      font-size: 0.95rem;
      margin-bottom: 1rem;
    }}
    .demo {{
      background: #161b22;
      border: 1px solid #21262d;
      border-radius: 8px;
      margin-bottom: 1.5rem;
      overflow: hidden;
    }}
    .demo-grid {{
      display: flex;
      flex-wrap: wrap;
    }}
    .demo-code {{
      flex: 0 0 420px;
      padding: 1.5rem;
      border-right: 1px solid #21262d;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }}
    .demo-code pre {{
      background: #0d1117;
      border: 1px solid #21262d;
      border-radius: 6px;
      padding: 1rem;
      overflow-x: auto;
      font-size: 0.85rem;
      line-height: 1.5;
    }}
    .demo-code code {{
      font-family: "SF Mono", "Fira Code", monospace;
      color: #c9d1d9;
    }}
    .timing {{
      color: #81c784;
      font-family: "SF Mono", "Fira Code", monospace;
      font-size: 0.85rem;
      margin-top: 0.8rem;
    }}
    .demo-images {{
      flex: 1;
      min-width: 500px;
      padding: 1rem;
    }}
    .comparison {{
      display: flex;
      gap: 0.5rem;
    }}
    .panel {{
      position: relative;
      flex: 1;
    }}
    .panel img {{
      width: 100%;
      border-radius: 4px;
      border: 1px solid #21262d;
    }}
    .label {{
      position: absolute;
      bottom: 6px;
      right: 6px;
      background: rgba(0,0,0,0.7);
      color: #c9d1d9;
      padding: 0.15rem 0.4rem;
      border-radius: 3px;
      font-size: 0.75rem;
    }}
    footer {{
      text-align: center;
      color: #484f58;
      margin-top: 2rem;
      font-size: 0.85rem;
    }}
    footer a {{ color: #484f58; }}
    @media (max-width: 900px) {{
      .demo-code {{ flex: 1 1 100%; border-right: none; border-bottom: 1px solid #21262d; }}
      .demo-images {{ min-width: unset; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>pyquadwild</h1>
    <p class="sub">Python bindings for <a href="https://github.com/cgg-bern/quadwild-bimdf">QuadWild BiMDF</a> &mdash; quad-dominant remeshing</p>
    <div class="install">pip install pyquadwild --find-links https://github.com/PozzettiAndrea/pyquadwild/releases/latest/download/</div>
    <p class="links">
      <a href="https://github.com/PozzettiAndrea/pyquadwild">GitHub</a> &middot;
      <a href="https://pypi.org/project/pyquadwild/">PyPI</a>
    </p>
  </header>

  {all_sections_html}

  <footer>
    Generated automatically by CI &middot;
    <a href="https://github.com/cgg-bern/quadwild-bimdf">QuadWild BiMDF</a> (CGG @ UniBE) &middot;
    <a href="https://github.com/nicopietroni/quadwild">QuadWild</a> (Pietroni et al., SIGGRAPH 2021)
  </footer>
</body>
</html>
"""
    with open(os.path.join(OUT_DIR, "index.html"), "w") as f:
        f.write(html)


def main():
    if os.path.exists(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR)

    verts, faces, mesh_name = get_mesh()
    sections = []

    # ── Quad Remeshing ────────────────────────────────────────────
    remesh_demos = []

    remesh_demos.append(run_demo("default",
        lambda v, f: pyquadwild.quadwild_remesh(v, f),
        verts, faces,
        textwrap.dedent(f"""\
            import pyquadwild
            import trimesh

            mesh = trimesh.load("{mesh_name}")
            v_quad, f_quad = pyquadwild.quadwild_remesh(
                mesh.vertices, mesh.faces,
            )"""),
        after_label="Quad Remeshed"))

    remesh_demos.append(run_demo("fine",
        lambda v, f: pyquadwild.quadwild_remesh(v, f, scale_factor=0.5),
        verts, faces,
        textwrap.dedent(f"""\
            # Finer quads (smaller scale factor)
            v, f = pyquadwild.quadwild_remesh(
                mesh.vertices, mesh.faces,
                scale_factor=0.5,
            )"""),
        after_label="Fine Quads"))

    remesh_demos.append(run_demo("coarse",
        lambda v, f: pyquadwild.quadwild_remesh(v, f, scale_factor=2.0),
        verts, faces,
        textwrap.dedent(f"""\
            # Coarser quads (larger scale factor)
            v, f = pyquadwild.quadwild_remesh(
                mesh.vertices, mesh.faces,
                scale_factor=2.0,
            )"""),
        after_label="Coarse Quads"))

    sections.append({
        "title": "Quad-Dominant Remeshing",
        "subtitle": "Feature-line driven quad remeshing via QuadWild with Bi-MDF solver",
        "demos": remesh_demos,
    })

    # ── Sharp Feature Preservation ────────────────────────────────
    sharp_demos = []

    sharp_demos.append(run_demo("sharp_low",
        lambda v, f: pyquadwild.quadwild_remesh(v, f, sharp_angle=15.0),
        verts, faces,
        textwrap.dedent(f"""\
            # Aggressive sharp detection (15 degrees)
            v, f = pyquadwild.quadwild_remesh(
                mesh.vertices, mesh.faces,
                sharp_angle=15.0,
            )"""),
        after_label="Sharp 15"))

    sharp_demos.append(run_demo("sharp_high",
        lambda v, f: pyquadwild.quadwild_remesh(v, f, sharp_angle=60.0),
        verts, faces,
        textwrap.dedent(f"""\
            # Relaxed sharp detection (60 degrees)
            v, f = pyquadwild.quadwild_remesh(
                mesh.vertices, mesh.faces,
                sharp_angle=60.0,
            )"""),
        after_label="Sharp 60"))

    sections.append({
        "title": "Sharp Feature Preservation",
        "subtitle": "Control edge flow alignment with sharp angle threshold",
        "demos": sharp_demos,
    })

    # ── Alpha (Regularity vs Isometry) ────────────────────────────
    alpha_demos = []

    alpha_demos.append(run_demo("alpha_low",
        lambda v, f: pyquadwild.quadwild_remesh(v, f, alpha=0.005),
        verts, faces,
        textwrap.dedent(f"""\
            # More regular quads (low alpha)
            v, f = pyquadwild.quadwild_remesh(
                mesh.vertices, mesh.faces,
                alpha=0.005,
            )"""),
        after_label="Regular (alpha=0.005)"))

    alpha_demos.append(run_demo("alpha_high",
        lambda v, f: pyquadwild.quadwild_remesh(v, f, alpha=0.1),
        verts, faces,
        textwrap.dedent(f"""\
            # Better feature alignment (high alpha)
            v, f = pyquadwild.quadwild_remesh(
                mesh.vertices, mesh.faces,
                alpha=0.1,
            )"""),
        after_label="Isometric (alpha=0.1)"))

    sections.append({
        "title": "Regularity vs Isometry",
        "subtitle": "Alpha controls the balance between regular quad shapes and feature alignment",
        "demos": alpha_demos,
    })

    generate_html(sections)

    # Preview image for README
    try:
        from PIL import Image
        d = remesh_demos[0]
        before = Image.open(os.path.join(OUT_DIR, f"{d['name']}_before.png"))
        after = Image.open(os.path.join(OUT_DIR, f"{d['name']}_after.png"))
        w, h = before.size
        grid = Image.new("RGB", (w * 2, h), "#0d1117")
        grid.paste(before, (0, 0))
        grid.paste(after, (w, 0))
        grid.save(os.path.join(OUT_DIR, "preview.png"))
    except Exception as e:
        print(f"Skipping preview: {e}")

    print(f"Demo: {OUT_DIR}/")
    for f in sorted(os.listdir(OUT_DIR)):
        sz = os.path.getsize(os.path.join(OUT_DIR, f))
        print(f"  {f} ({sz // 1024}KB)")


if __name__ == "__main__":
    main()
