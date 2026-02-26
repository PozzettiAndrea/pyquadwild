// Python bindings for QuadWild BiMDF quad-dominant remeshing via nanobind.
//
// This file ONLY includes nanobind and the pipeline wrapper header.
// All VCG/QuadWild headers are isolated in pipeline.cpp to avoid
// conflicts between Python's structmember.h and VCG's plylib.h.

#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <nanobind/stl/string.h>
#include <cstring>

#include "array_support.h"
#include "pipeline.h"

namespace nb = nanobind;

static nb::tuple py_quadwild_remesh(
    const NDArray<const double, 2> vertices,
    const NDArray<const int, 2> faces,
    bool do_remesh,
    float sharp_angle,
    float alpha,
    float scale_fact,
    bool smooth
) {
    if (vertices.shape(1) != 3) {
        throw std::runtime_error("vertices must have shape (N, 3)");
    }
    if (faces.shape(1) != 3) {
        throw std::runtime_error("faces must have shape (M, 3) — input must be a triangle mesh");
    }
    if (vertices.shape(0) == 0 || faces.shape(0) == 0) {
        throw std::runtime_error("Input mesh is empty");
    }

    QuadWildResult result = run_quadwild_pipeline(
        vertices.data(), static_cast<int>(vertices.shape(0)),
        faces.data(), static_cast<int>(faces.shape(0)),
        do_remesh, sharp_angle, alpha, scale_fact, smooth
    );

    // Convert result to numpy arrays
    NDArray<double, 2> verts_arr = MakeNDArray<double, 2>(
        {result.num_vertices, 3});
    std::memcpy(verts_arr.data(), result.vertices.data(),
        result.num_vertices * 3 * sizeof(double));

    NDArray<int, 2> faces_arr = MakeNDArray<int, 2>(
        {result.num_faces, result.face_width});
    std::memcpy(faces_arr.data(), result.faces.data(),
        result.num_faces * result.face_width * sizeof(int));

    return nb::make_tuple(verts_arr, faces_arr);
}


NB_MODULE(_pyquadwild, m) {
    m.doc() = "Python bindings for QuadWild BiMDF quad-dominant remeshing";

    m.def("quadwild_remesh", &py_quadwild_remesh,
        R"doc(
Quad-dominant remeshing using QuadWild with Bi-MDF solver.

Runs the full 3-step QuadWild pipeline:
1. Field computation and optional isotropic remeshing
2. Field-line tracing to find quad patches
3. Quadrangulation from patches using ILP solver

Parameters
----------
vertices : ndarray, shape (N, 3), dtype float64
    Input triangle mesh vertex positions.
faces : ndarray, shape (M, 3), dtype int32
    Input triangle mesh face indices (0-based).
do_remesh : bool
    If True, remesh the input before field computation.
sharp_angle : float
    Dihedral angle threshold (degrees) for sharp feature detection.
alpha : float
    Balance between regularity and isometry. Range: 0.005-0.1.
scale_fact : float
    Scale factor for quad size. Larger = bigger quads.
smooth : bool
    If True, smooth the output mesh after quadrangulation.

Returns
-------
vertices : ndarray, shape (K, 3), dtype float64
    Output quad mesh vertex positions.
faces : ndarray, shape (L, 4), dtype int32
    Output quad mesh face indices (0-based). Unused slots are -1.
)doc",
        nb::arg("vertices"),
        nb::arg("faces"),
        nb::arg("do_remesh") = true,
        nb::arg("sharp_angle") = 35.0f,
        nb::arg("alpha") = 0.02f,
        nb::arg("scale_fact") = 1.0f,
        nb::arg("smooth") = true
    );
}
