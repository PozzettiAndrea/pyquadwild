# pyquadwild

Python bindings for [QuadWild BiMDF](https://github.com/cgg-bern/quadwild-bimdf) — quad-dominant remeshing.

Converts triangle meshes into high-quality quad-dominant meshes with feature-line preservation, using the algorithm from:

> *Reliable Feature-Line Driven Quad-Remeshing* (Pietroni et al., SIGGRAPH 2021)

Extended with the Bi-MDF solver from [CGG @ University of Bern](https://github.com/cgg-bern).

## Installation

```bash
pip install pyquadwild --find-links https://github.com/PozzettiAndrea/pyquadwild/releases/latest/download/
```

## Usage

```python
import numpy as np
import pyquadwild

# Load a triangle mesh (e.g. via trimesh)
import trimesh
mesh = trimesh.load("model.obj")

# Quad-dominant remeshing
v_quad, f_quad = pyquadwild.quadwild_remesh(
    mesh.vertices, mesh.faces,
    sharp_angle=35.0,   # Feature edge detection threshold
    alpha=0.02,         # Regularity vs isometry balance
    scale_factor=1.0,   # Quad size (larger = fewer quads)
)

print(f"Output: {len(v_quad)} vertices, {len(f_quad)} quad faces")
# f_quad has shape (M, 4) — each row is a quad face
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `remesh` | `True` | Pre-remesh input for better triangle quality |
| `sharp_angle` | `35.0` | Dihedral angle threshold for sharp features (degrees) |
| `alpha` | `0.02` | Regularity (low) vs isometry (high). Range: 0.005–0.1 |
| `scale_factor` | `1.0` | Quad size multiplier. Larger = bigger quads |
| `smooth` | `True` | Apply topology smoothing after quadrangulation |

## License

GPL-3.0-or-later (same as QuadWild)
