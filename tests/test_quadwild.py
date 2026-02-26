"""Tests for pyquadwild: QuadWild BiMDF quad-dominant remeshing."""

import numpy as np
import pytest


def make_icosphere(subdivisions=2):
    """Create a subdivided icosphere for testing.

    QuadWild needs sufficient geometry to produce good results,
    so we subdivide the base icosahedron.
    """
    phi = (1.0 + np.sqrt(5.0)) / 2.0

    vertices = np.array([
        [-1, phi, 0], [1, phi, 0], [-1, -phi, 0], [1, -phi, 0],
        [0, -1, phi], [0, 1, phi], [0, -1, -phi], [0, 1, -phi],
        [phi, 0, -1], [phi, 0, 1], [-phi, 0, -1], [-phi, 0, 1],
    ], dtype=np.float64)

    norms = np.linalg.norm(vertices, axis=1, keepdims=True)
    vertices = vertices / norms

    faces = np.array([
        [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
        [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
        [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
        [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1],
    ], dtype=np.int32)

    # Subdivide to get enough geometry
    for _ in range(subdivisions):
        vertices, faces = _subdivide(vertices, faces)

    return vertices, faces


def _subdivide(vertices, faces):
    """Loop-style midpoint subdivision."""
    edge_midpoints = {}
    new_verts = list(vertices)
    new_faces = []

    def get_midpoint(i, j):
        key = (min(i, j), max(i, j))
        if key in edge_midpoints:
            return edge_midpoints[key]
        mid = (vertices[i] + vertices[j]) / 2.0
        mid = mid / np.linalg.norm(mid)  # project onto sphere
        idx = len(new_verts)
        new_verts.append(mid)
        edge_midpoints[key] = idx
        return idx

    for f in faces:
        a, b, c = f
        ab = get_midpoint(a, b)
        bc = get_midpoint(b, c)
        ca = get_midpoint(c, a)
        new_faces.append([a, ab, ca])
        new_faces.append([b, bc, ab])
        new_faces.append([c, ca, bc])
        new_faces.append([ab, bc, ca])

    return np.array(new_verts, dtype=np.float64), np.array(new_faces, dtype=np.int32)


def make_cube():
    """Create a triangulated cube mesh."""
    vertices = np.array([
        [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
        [-1, -1,  1], [1, -1,  1], [1, 1,  1], [-1, 1,  1],
    ], dtype=np.float64)

    # 12 triangles (2 per face of cube)
    faces = np.array([
        [0, 1, 2], [0, 2, 3],  # bottom
        [4, 6, 5], [4, 7, 6],  # top
        [0, 5, 1], [0, 4, 5],  # front
        [2, 7, 3], [2, 6, 7],  # back
        [0, 3, 7], [0, 7, 4],  # left
        [1, 5, 6], [1, 6, 2],  # right
    ], dtype=np.int32)

    return vertices, faces


def make_subdivided_cube(subdivisions=3):
    """Create a subdivided cube (no sphere projection)."""
    vertices, faces = make_cube()
    for _ in range(subdivisions):
        vertices, faces = _subdivide_flat(vertices, faces)
    return vertices, faces


def _subdivide_flat(vertices, faces):
    """Midpoint subdivision without sphere projection."""
    edge_midpoints = {}
    new_verts = list(vertices)
    new_faces = []

    def get_midpoint(i, j):
        key = (min(i, j), max(i, j))
        if key in edge_midpoints:
            return edge_midpoints[key]
        mid = (vertices[i] + vertices[j]) / 2.0
        idx = len(new_verts)
        new_verts.append(mid)
        edge_midpoints[key] = idx
        return idx

    for f in faces:
        a, b, c = f
        ab = get_midpoint(a, b)
        bc = get_midpoint(b, c)
        ca = get_midpoint(c, a)
        new_faces.append([a, ab, ca])
        new_faces.append([b, bc, ab])
        new_faces.append([c, ca, bc])
        new_faces.append([ab, bc, ca])

    return np.array(new_verts, dtype=np.float64), np.array(new_faces, dtype=np.int32)


# ── Basic Remeshing ──────────────────────────────────────────────────


def test_quadwild_basic():
    """Test basic quad remeshing round-trip."""
    import pyquadwild

    verts, faces = make_icosphere(subdivisions=2)
    v_out, f_out = pyquadwild.quadwild_remesh(verts, faces)

    assert isinstance(v_out, np.ndarray)
    assert isinstance(f_out, np.ndarray)
    assert v_out.ndim == 2
    assert f_out.ndim == 2
    assert v_out.shape[1] == 3
    # Output should be quads (4 vertices per face)
    assert f_out.shape[1] == 4
    assert len(v_out) > 0
    assert len(f_out) > 0


def test_quadwild_output_is_quads():
    """Verify output faces are mostly quads."""
    import pyquadwild

    verts, faces = make_icosphere(subdivisions=2)
    v_out, f_out = pyquadwild.quadwild_remesh(verts, faces)

    # Count actual quads (no -1 padding in 4th index)
    is_quad = f_out[:, 3] >= 0
    quad_ratio = np.sum(is_quad) / len(f_out)

    # QuadWild should produce mostly quads (>80%)
    assert quad_ratio > 0.8, f"Only {quad_ratio:.1%} of faces are quads"


def test_quadwild_preserves_scale():
    """Test that remeshing roughly preserves the bounding box."""
    import pyquadwild

    verts, faces = make_icosphere(subdivisions=2)
    v_out, f_out = pyquadwild.quadwild_remesh(verts, faces)

    original_extent = np.max(np.abs(verts))
    remeshed_extent = np.max(np.abs(v_out))
    assert abs(remeshed_extent - original_extent) < 0.3


def test_quadwild_custom_sharp_angle():
    """Test with different sharp angle thresholds."""
    import pyquadwild

    verts, faces = make_subdivided_cube(subdivisions=3)
    v_out, f_out = pyquadwild.quadwild_remesh(
        verts, faces, sharp_angle=25.0
    )

    assert v_out.shape[1] == 3
    assert f_out.shape[1] == 4
    assert len(v_out) > 0


def test_quadwild_custom_alpha():
    """Test with different alpha values."""
    import pyquadwild

    verts, faces = make_icosphere(subdivisions=2)
    v_out, f_out = pyquadwild.quadwild_remesh(
        verts, faces, alpha=0.005
    )

    assert v_out.shape[1] == 3
    assert f_out.shape[1] == 4
    assert len(v_out) > 0


def test_quadwild_scale_factor():
    """Test that scale_factor affects output density."""
    import pyquadwild

    verts, faces = make_icosphere(subdivisions=2)

    _, f_small = pyquadwild.quadwild_remesh(verts, faces, scale_factor=0.5)
    _, f_large = pyquadwild.quadwild_remesh(verts, faces, scale_factor=2.0)

    # Smaller scale factor should produce more faces
    assert len(f_small) > len(f_large)


# ── Input Validation ─────────────────────────────────────────────────


def test_quadwild_input_validation_vertex_shape():
    """Test that invalid vertex shape raises error."""
    import pyquadwild

    bad_verts = np.zeros((10, 2), dtype=np.float64)
    good_faces = np.zeros((5, 3), dtype=np.int32)

    with pytest.raises((ValueError, RuntimeError)):
        pyquadwild.quadwild_remesh(bad_verts, good_faces)


def test_quadwild_input_validation_face_shape():
    """Test that non-triangle face input raises error."""
    import pyquadwild

    good_verts = np.zeros((10, 3), dtype=np.float64)
    bad_faces = np.zeros((5, 4), dtype=np.int32)  # quads, not tris

    with pytest.raises((ValueError, RuntimeError)):
        pyquadwild.quadwild_remesh(good_verts, bad_faces)


def test_quadwild_input_validation_empty():
    """Test that empty mesh raises error."""
    import pyquadwild

    with pytest.raises((ValueError, RuntimeError)):
        pyquadwild.quadwild_remesh(
            np.zeros((0, 3), dtype=np.float64),
            np.zeros((0, 3), dtype=np.int32),
        )
