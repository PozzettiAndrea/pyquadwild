"""Tests for pyquadwild: QuadWild BiMDF quad-dominant remeshing."""

import numpy as np
import pytest


# ── Basic Remeshing ──────────────────────────────────────────────────


def test_quadwild_basic(icosphere):
    """Test basic quad remeshing round-trip."""
    import pyquadwild

    verts, faces = icosphere
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


def test_quadwild_output_is_quads(icosphere):
    """Verify output faces are mostly quads."""
    import pyquadwild

    verts, faces = icosphere
    v_out, f_out = pyquadwild.quadwild_remesh(verts, faces)

    # Count actual quads (no -1 padding in 4th index)
    is_quad = f_out[:, 3] >= 0
    quad_ratio = np.sum(is_quad) / len(f_out)

    # QuadWild should produce mostly quads (>80%)
    assert quad_ratio > 0.8, f"Only {quad_ratio:.1%} of faces are quads"


def test_quadwild_preserves_scale(icosphere):
    """Test that remeshing roughly preserves the bounding box."""
    import pyquadwild

    verts, faces = icosphere
    v_out, f_out = pyquadwild.quadwild_remesh(verts, faces)

    original_extent = np.max(np.abs(verts))
    remeshed_extent = np.max(np.abs(v_out))
    assert abs(remeshed_extent - original_extent) < 0.3


def test_quadwild_custom_sharp_angle(cube):
    """Test with different sharp angle thresholds."""
    import pyquadwild

    verts, faces = cube
    v_out, f_out = pyquadwild.quadwild_remesh(
        verts, faces, sharp_angle=25.0
    )

    assert v_out.shape[1] == 3
    assert f_out.shape[1] == 4
    assert len(v_out) > 0


def test_quadwild_custom_alpha(icosphere):
    """Test with different alpha values."""
    import pyquadwild

    verts, faces = icosphere
    v_out, f_out = pyquadwild.quadwild_remesh(
        verts, faces, alpha=0.005
    )

    assert v_out.shape[1] == 3
    assert f_out.shape[1] == 4
    assert len(v_out) > 0


def test_quadwild_scale_factor(icosphere):
    """Test that scale_factor affects output density."""
    import pyquadwild

    verts, faces = icosphere

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
