# SPDX-License-Identifier: GPL-3.0-or-later
"""QuadWild BiMDF quad-dominant remeshing wrapper."""

import numpy as np
from numpy.typing import NDArray

from pyquadwild._pyquadwild import quadwild_remesh as _quadwild_remesh


def quadwild_remesh(
    vertices: NDArray[np.float64],
    faces: NDArray[np.int32],
    *,
    remesh: bool = True,
    sharp_angle: float = 35.0,
    alpha: float = 0.02,
    scale_factor: float = 1.0,
    smooth: bool = True,
) -> tuple[NDArray[np.float64], NDArray[np.int32]]:
    """Quad-dominant remeshing using QuadWild with Bi-MDF solver.

    Runs the full 3-step QuadWild pipeline:
      1. Field computation and optional isotropic remeshing
      2. Field-line tracing to find quad patches
      3. Quadrangulation from patches using ILP solver

    Parameters
    ----------
    vertices : ndarray, shape (N, 3)
        Input triangle mesh vertex positions.
    faces : ndarray, shape (M, 3)
        Input triangle mesh face indices (0-based).
    remesh : bool, default True
        If True, remesh the input before field computation.
        Recommended for meshes with poor triangle quality.
    sharp_angle : float, default 35.0
        Dihedral angle threshold (degrees) for sharp feature detection.
        Edges with angle above this are preserved as sharp creases.
    alpha : float, default 0.02
        Balance between regularity and isometry of the quad layout.
        Lower values produce more regular quads; higher values allow
        more singularities for better feature alignment.
        Typical range: 0.005 to 0.1.
    scale_factor : float, default 1.0
        Scale factor for quad size. Larger values produce bigger quads
        (fewer output faces).
    smooth : bool, default True
        If True, smooth the output mesh topology after quadrangulation.

    Returns
    -------
    vertices : ndarray, shape (K, 3), dtype float64
        Output quad mesh vertex positions.
    faces : ndarray, shape (L, 4), dtype int32
        Output quad mesh face indices (0-based).
        For non-quad faces (rare), unused indices are set to -1.

    Examples
    --------
    >>> import numpy as np
    >>> import pyquadwild
    >>> # Load a triangle mesh (e.g. via trimesh)
    >>> v_quad, f_quad = pyquadwild.quadwild_remesh(vertices, faces)
    >>> print(f"Quads: {f_quad.shape[0]}, vertices: {v_quad.shape[0]}")
    """
    v = np.ascontiguousarray(vertices, dtype=np.float64)
    f = np.ascontiguousarray(faces, dtype=np.int32)

    if v.ndim != 2 or v.shape[1] != 3:
        raise ValueError(f"vertices must have shape (N, 3), got {v.shape}")
    if f.ndim != 2 or f.shape[1] != 3:
        raise ValueError(f"faces must have shape (M, 3), got {f.shape}")
    if len(v) == 0 or len(f) == 0:
        raise ValueError("Input mesh is empty")

    return _quadwild_remesh(
        v, f,
        do_remesh=remesh,
        sharp_angle=float(sharp_angle),
        alpha=float(alpha),
        scale_fact=float(scale_factor),
        smooth=smooth,
    )
