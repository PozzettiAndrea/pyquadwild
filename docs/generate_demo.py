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
    if mesh.n_points > 0:
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


TEMPLATE_DIR = os.path.dirname(__file__)


def html_escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _render_demo(d):
    code_html = html_escape(d["code"])
    label = d.get("after_label", "Output")
    return f"""
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
    </section>"""


def generate_html(sections):
    sections_html = ""
    for section in sections:
        sections_html += f"""
    <h2 class="section-title">{section['title']}</h2>
    <p class="section-sub">{section['subtitle']}</p>"""
        for d in section["demos"]:
            sections_html += _render_demo(d)

    with open(os.path.join(TEMPLATE_DIR, "template.html")) as f:
        template = f.read()

    html = template.replace("{{sections}}", sections_html)

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
