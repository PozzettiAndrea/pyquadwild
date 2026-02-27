"""Shared test fixtures — load mesh assets from tests/assets/."""

import struct
from pathlib import Path

import numpy as np
import pytest

ASSETS_DIR = Path(__file__).parent / "assets"


def load_binary_stl(path):
    """Load a binary STL file, return (vertices, faces) as numpy arrays."""
    with open(path, "rb") as f:
        f.read(80)  # header
        (num_tris,) = struct.unpack("<I", f.read(4))

        all_verts = []
        faces = []
        vert_map = {}

        for _ in range(num_tris):
            f.read(12)  # normal
            tri_indices = []
            for _ in range(3):
                coords = struct.unpack("<fff", f.read(12))
                key = coords
                if key not in vert_map:
                    vert_map[key] = len(all_verts)
                    all_verts.append(coords)
                tri_indices.append(vert_map[key])
            faces.append(tri_indices)
            f.read(2)  # attribute

    return (
        np.array(all_verts, dtype=np.float64),
        np.array(faces, dtype=np.int32),
    )


@pytest.fixture
def icosphere():
    """Subdivided icosphere (162 verts, 320 tris)."""
    return load_binary_stl(ASSETS_DIR / "icosphere.stl")


@pytest.fixture
def cube():
    """Subdivided cube (386 verts, 768 tris)."""
    return load_binary_stl(ASSETS_DIR / "cube.stl")
