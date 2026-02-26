cmake_minimum_required(VERSION 3.15...3.26)
project(pyquadwild LANGUAGES C CXX)

# ---------------------------------------------------------------------------
# Configure quadwild-bimdf as static libraries
# ---------------------------------------------------------------------------
set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED TRUE)
set(CMAKE_CXX_EXTENSIONS FALSE)

# Disable optional deps we don't need
set(QUADRETOPOLOGY_WITH_GUROBI OFF CACHE BOOL "" FORCE)
set(SATSUMA_ENABLE_BLOSSOM5 OFF CACHE BOOL "" FORCE)
set(WANT_COMISO_QT OFF CACHE BOOL "" FORCE)
set(DISABLE_MPI ON CACHE BOOL "" FORCE)
set(COMISO_ENABLE_METIS OFF CACHE BOOL "" FORCE)
set(COMISO_ENABLE_MUMPS OFF CACHE BOOL "" FORCE)
set(COMISO_ENABLE_LPSOLVE OFF CACHE BOOL "" FORCE)
set(COMISO_ENABLE_GUROBI OFF CACHE BOOL "" FORCE)
set(COMISO_BUILD_WITHOUT_BOOST ON CACHE BOOL "" FORCE)
set(OPENMESH_BUILD_SHARED OFF CACHE BOOL "" FORCE)

if(WIN32)
  add_definitions(/D_USE_MATH_DEFINES /DNOMINMAX /DHETYPE=auto)
  set(CMAKE_MSVC_RUNTIME_LIBRARY MultiThreaded)
endif()

# Build quadwild-bimdf — EXCLUDE_FROM_ALL suppresses its install rules
add_subdirectory(quadwild-bimdf EXCLUDE_FROM_ALL)

# ---------------------------------------------------------------------------
# Python + nanobind
# ---------------------------------------------------------------------------
find_package(Python 3.10
  REQUIRED COMPONENTS Interpreter Development.Module
  OPTIONAL_COMPONENTS Development.SABIModule)

find_package(nanobind CONFIG REQUIRED)

# ---------------------------------------------------------------------------
# Static library for QuadWild pipeline (pure C++ — NO Python headers)
# This isolation prevents VCG plylib.h / Python structmember.h macro conflicts.
# ---------------------------------------------------------------------------
add_library(quadwild_pipeline STATIC
  src/pipeline.cpp
  quadwild-bimdf/quadwild/trace.cpp
)

target_link_libraries(quadwild_pipeline PUBLIC
  quadwild::quadretopology
  quadwild::lib_field_computation
  quadwild::quad_from_patches
  vcglib::vcglib
)

find_package(OpenMP QUIET)
if(OpenMP_CXX_FOUND)
  target_link_libraries(quadwild_pipeline PUBLIC OpenMP::OpenMP_CXX)
endif()

target_include_directories(quadwild_pipeline PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/src
  # quadwild headers
  ${CMAKE_CURRENT_SOURCE_DIR}/quadwild-bimdf/quadwild
  ${CMAKE_CURRENT_SOURCE_DIR}/quadwild-bimdf/components/field_computation
  ${CMAKE_CURRENT_SOURCE_DIR}/quadwild-bimdf/components/quad_from_patches
  # vcglib, eigen, libigl
  ${CMAKE_CURRENT_SOURCE_DIR}/quadwild-bimdf/libs/vcglib
  ${CMAKE_CURRENT_SOURCE_DIR}/quadwild-bimdf/libs/eigen
  ${CMAKE_CURRENT_SOURCE_DIR}/quadwild-bimdf/libs/libigl/include
  # xfield_tracer
  ${CMAKE_CURRENT_SOURCE_DIR}/quadwild-bimdf/libs/xfield_tracer
)

target_compile_definitions(quadwild_pipeline PUBLIC COMISO_FIELD)

# ---------------------------------------------------------------------------
# Nanobind extension module (Python + nanobind ONLY — no VCG headers)
# ---------------------------------------------------------------------------
nanobind_add_module(
  _pyquadwild
  STABLE_ABI
  src/_pyquadwild.cpp
)

# Link the pipeline library — only pipeline.h is included, no VCG leaks
target_link_libraries(_pyquadwild PRIVATE quadwild_pipeline)

target_include_directories(_pyquadwild PRIVATE
  ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# Compiler-specific optimization
if(MSVC)
  target_compile_options(_pyquadwild PRIVATE /O2)
else()
  target_compile_options(_pyquadwild PRIVATE -O3)
endif()

# Install into the pyquadwild Python package directory
install(TARGETS _pyquadwild LIBRARY DESTINATION pyquadwild)
