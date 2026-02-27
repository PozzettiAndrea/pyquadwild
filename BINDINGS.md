# Binding Coverage

## Mapped

| Function | Description |
|----------|-------------|
| `quadwild_remesh` | Full pipeline: remesh → field computation → tracing → quadrangulation |

### Parameters Exposed

| Parameter | Description |
|-----------|-------------|
| `remesh` | Pre-remesh input for better triangle quality |
| `sharp_angle` | Dihedral angle threshold for sharp feature detection |
| `alpha` | Balance between regularity and isometry |
| `scale_factor` | Quad size multiplier |
| `smooth` | Topology smoothing after quadrangulation |

## Not Mapped

| Capability | Notes |
|------------|-------|
| `remeshAndField` independently | Step 1: field computation without full pipeline |
| `trace` independently | Step 2: field-line tracing without full pipeline |
| `quadrangulate` independently | Step 3: ILP quad layout without full pipeline |
| Intermediate data access | Directional field, patch structure, sharp features |
| Manual feature file input | Load `.sharp` files for custom feature lines |
| Manual field file input | Load pre-computed directional fields |
| ILP solver tuning | Advanced BiMDF solver parameters |
| Intermediate mesh export | Save remeshed / traced meshes separately |
