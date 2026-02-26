// Pure C++ wrapper for the QuadWild pipeline.
// This header MUST NOT include any Python/nanobind headers to avoid
// conflicts between Python's structmember.h and VCG's plylib.h.

#ifndef PYQUADWILD_PIPELINE_H
#define PYQUADWILD_PIPELINE_H

#include <vector>
#include <string>

struct QuadWildResult {
    std::vector<double> vertices;   // flat: [x0,y0,z0, x1,y1,z1, ...]
    std::vector<int> faces;         // flat: [v0,v1,v2,v3, ...] per face
    int num_vertices;
    int num_faces;
    int face_width;                 // typically 4 for quads
};

// Run the full QuadWild BiMDF pipeline.
// Input: triangle mesh as flat arrays.
// Output: quad-dominant mesh.
QuadWildResult run_quadwild_pipeline(
    const double* vertices, int num_vertices,
    const int* faces, int num_faces,
    bool do_remesh,
    float sharp_angle,
    float alpha,
    float scale_fact,
    bool smooth
);

#endif // PYQUADWILD_PIPELINE_H
