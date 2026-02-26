// Pure C++ implementation of the QuadWild pipeline.
// NO Python/nanobind headers here — avoids VCG/Python macro conflicts.

#include "pipeline.h"

#include <clocale>
#include <iostream>
#include <fstream>
#include <stdexcept>
#include <filesystem>
#include <random>
#include <algorithm>

// QuadWild / VCG headers
#include <triangle_mesh_type.h>
#include <mesh_types.h>
#include <tracing/mesh_type.h>
#include <vcg/complex/complex.h>
#include <wrap/io_trimesh/import_obj.h>
#include <wrap/io_trimesh/export_obj.h>

#include "functions.h"
#include "trace.h"

namespace fs = std::filesystem;

// --------------------------------------------------------------------------
// RAII helper for temp directory
// --------------------------------------------------------------------------
struct TempDir {
    fs::path path;

    TempDir() {
        auto base = fs::temp_directory_path() / "pyquadwild";
        fs::create_directories(base);

        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_int_distribution<uint64_t> dist;
        for (int attempt = 0; attempt < 100; ++attempt) {
            auto candidate = base / std::to_string(dist(gen));
            if (fs::create_directory(candidate)) {
                path = candidate;
                return;
            }
        }
        throw std::runtime_error("Failed to create temporary directory");
    }

    ~TempDir() {
        try { fs::remove_all(path); } catch (...) {}
    }

    TempDir(const TempDir&) = delete;
    TempDir& operator=(const TempDir&) = delete;
};

// --------------------------------------------------------------------------
// Write mesh to OBJ
// --------------------------------------------------------------------------
static void write_obj(
    const double* verts, int nv,
    const int* faces, int nf,
    const std::string& path
) {
    std::ofstream out(path);
    if (!out.is_open()) {
        throw std::runtime_error("Failed to open " + path + " for writing");
    }

    out << std::fixed;
    for (int i = 0; i < nv; ++i) {
        out << "v " << verts[i*3+0] << " " << verts[i*3+1] << " " << verts[i*3+2] << "\n";
    }
    for (int i = 0; i < nf; ++i) {
        out << "f " << (faces[i*3+0]+1) << " " << (faces[i*3+1]+1) << " " << (faces[i*3+2]+1) << "\n";
    }
    out.close();
}

// --------------------------------------------------------------------------
// Extract vertices/faces from VCG PolyMesh
// --------------------------------------------------------------------------
static QuadWildResult extract_polymesh(const PolyMesh& mesh) {
    QuadWildResult result;

    // Build vertex index remap (skip deleted)
    std::vector<int> vert_remap(mesh.vert.size(), -1);
    int nv = 0;
    for (size_t i = 0; i < mesh.vert.size(); ++i) {
        if (!mesh.vert[i].IsD()) {
            vert_remap[i] = nv++;
        }
    }

    // Count faces and determine max face width
    int nf = 0;
    int max_vn = 0;
    for (size_t i = 0; i < mesh.face.size(); ++i) {
        if (!mesh.face[i].IsD()) {
            nf++;
            int vn = mesh.face[i].VN();
            if (vn > max_vn) max_vn = vn;
        }
    }

    if (nv == 0 || nf == 0) {
        throw std::runtime_error("QuadWild produced an empty mesh");
    }

    int face_width = std::max(max_vn, 3);

    result.num_vertices = nv;
    result.num_faces = nf;
    result.face_width = face_width;
    result.vertices.resize(nv * 3);
    result.faces.resize(nf * face_width, -1);

    // Fill vertices
    int vi = 0;
    for (size_t i = 0; i < mesh.vert.size(); ++i) {
        if (mesh.vert[i].IsD()) continue;
        const auto& p = mesh.vert[i].cP();
        result.vertices[vi*3+0] = static_cast<double>(p[0]);
        result.vertices[vi*3+1] = static_cast<double>(p[1]);
        result.vertices[vi*3+2] = static_cast<double>(p[2]);
        vi++;
    }

    // Fill faces
    int fi = 0;
    for (size_t i = 0; i < mesh.face.size(); ++i) {
        if (mesh.face[i].IsD()) continue;
        int vn = mesh.face[i].VN();
        for (int j = 0; j < vn && j < face_width; ++j) {
            int orig_idx = static_cast<int>(
                mesh.face[i].cV(j) - &mesh.vert[0]
            );
            result.faces[fi * face_width + j] = vert_remap[orig_idx];
        }
        fi++;
    }

    return result;
}

// --------------------------------------------------------------------------
// Main pipeline
// --------------------------------------------------------------------------
QuadWildResult run_quadwild_pipeline(
    const double* vertices, int num_vertices,
    const int* faces, int num_faces,
    bool do_remesh,
    float sharp_angle,
    float alpha,
    float scale_fact,
    bool smooth
) {
    if (num_vertices <= 0 || num_faces <= 0) {
        throw std::runtime_error("Input mesh is empty");
    }

    // Ensure numeric locale is correct
    std::setlocale(LC_NUMERIC, "C");

    // Create temp directory
    TempDir tmpdir;
    std::string mesh_path = (tmpdir.path / "input.obj").string();
    std::string mesh_prefix = (tmpdir.path / "input").string();

    // Write input mesh
    write_obj(vertices, num_vertices, faces, num_faces, mesh_path);

    // Step 1: Load and remesh+field
    FieldTriMesh trimesh;
    bool allQuad;
    bool loaded = trimesh.LoadTriMesh(mesh_path, allQuad);
    if (!loaded) {
        throw std::runtime_error("Failed to load mesh into QuadWild");
    }
    trimesh.UpdateDataStructures();

    Parameters parameters;
    parameters.remesh = do_remesh;
    parameters.sharpAngle = sharp_angle;
    parameters.alpha = alpha;
    parameters.scaleFact = scale_fact;
    parameters.hasFeature = false;
    parameters.hasField = false;

    std::string sharpFilename;
    std::string fieldFilename;

    remeshAndField(trimesh, parameters, mesh_path, sharpFilename, fieldFilename);

    // Step 2: Tracing
    std::string rem_prefix = mesh_prefix + "_rem";
    TraceMesh traceTrimesh;
    bool trace_ok = trace(rem_prefix, traceTrimesh);
    if (!trace_ok) {
        throw std::runtime_error("QuadWild tracing step failed");
    }

    // Step 3: Quadrangulation
    TriangleMesh trimeshToQuadrangulate;
    std::vector<std::vector<size_t>> trimeshPartitions;
    std::vector<std::vector<size_t>> trimeshCorners;
    std::vector<std::pair<size_t,size_t>> trimeshFeatures;
    std::vector<size_t> trimeshFeaturesC;
    PolyMesh quadmesh;
    std::vector<std::vector<size_t>> quadmeshPartitions;
    std::vector<std::vector<size_t>> quadmeshCorners;
    std::vector<int> ilpResult;

    quadrangulate(
        rem_prefix + ".obj",
        trimeshToQuadrangulate, quadmesh,
        trimeshPartitions, trimeshCorners,
        trimeshFeatures, trimeshFeaturesC,
        quadmeshPartitions, quadmeshCorners,
        ilpResult, parameters
    );

    return extract_polymesh(quadmesh);
}
