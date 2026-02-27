"""Patch outdated CMake files in quadwild-bimdf submodule.

Fix 1: lemon sets CMP0048 to OLD, which newer CMake rejects.
Fix 2: lemon missing CMAKE_MODULE_LINKER_FLAGS_MAINTAINER (fails on Windows).
Fix 3: json requires cmake_minimum_required 3.1, which is too old.
Fix 4: OpenMesh requires cmake_minimum_required 3.3.0, which is too old.
"""
from pathlib import Path


def patch(path, old, new, label):
    content = path.read_text()
    if old in content:
        path.write_text(content.replace(old, new))
        print("Patched %s: %s" % (path, label))
    else:
        print("Already patched: %s" % path)


root = Path(__file__).resolve().parent.parent
libs = root / "quadwild-bimdf" / "libs"

patch(
    libs / "lemon" / "CMakeLists.txt",
    "CMAKE_POLICY(SET CMP0048 OLD)",
    "CMAKE_POLICY(SET CMP0048 NEW)",
    "CMP0048 OLD -> NEW",
)

# lemon defines a custom MAINTAINER build type but forgets MODULE_LINKER flags,
# which CMake requires on Windows. Insert them after each SHARED_LINKER block.
lemon_cmake = libs / "lemon" / "CMakeLists.txt"
content = lemon_cmake.read_text()
msvc_insert = '''  SET( CMAKE_SHARED_LINKER_FLAGS_MAINTAINER
    "${CMAKE_SHARED_LINKER_FLAGS_DEBUG}" CACHE STRING
    "Flags used by the shared libraries linker during maintainer builds."
     FORCE
    )
ELSE()'''
msvc_replacement = '''  SET( CMAKE_SHARED_LINKER_FLAGS_MAINTAINER
    "${CMAKE_SHARED_LINKER_FLAGS_DEBUG}" CACHE STRING
    "Flags used by the shared libraries linker during maintainer builds."
     FORCE
    )
  SET( CMAKE_MODULE_LINKER_FLAGS_MAINTAINER
    "${CMAKE_MODULE_LINKER_FLAGS_DEBUG}" CACHE STRING
    "Flags used by the module linker during maintainer builds." FORCE
    )
ELSE()'''
unix_insert = '''  SET( CMAKE_SHARED_LINKER_FLAGS_MAINTAINER
    "${CMAKE_SHARED_LINKER_FLAGS_DEBUG}" CACHE STRING
    "Flags used by the shared libraries linker during maintainer builds." FORCE)
ENDIF()'''
unix_replacement = '''  SET( CMAKE_SHARED_LINKER_FLAGS_MAINTAINER
    "${CMAKE_SHARED_LINKER_FLAGS_DEBUG}" CACHE STRING
    "Flags used by the shared libraries linker during maintainer builds." FORCE)
  SET( CMAKE_MODULE_LINKER_FLAGS_MAINTAINER
    "${CMAKE_MODULE_LINKER_FLAGS_DEBUG}" CACHE STRING
    "Flags used by the module linker during maintainer builds." FORCE)
ENDIF()'''
if msvc_insert in content:
    content = content.replace(msvc_insert, msvc_replacement)
    content = content.replace(unix_insert, unix_replacement)
    lemon_cmake.write_text(content)
    print("Patched %s: added CMAKE_MODULE_LINKER_FLAGS_MAINTAINER" % lemon_cmake)
else:
    print("Already patched: %s (MODULE_LINKER)" % lemon_cmake)

patch(
    libs / "json" / "CMakeLists.txt",
    "cmake_minimum_required(VERSION 3.1)",
    "cmake_minimum_required(VERSION 3.15)",
    "cmake_minimum_required 3.1 -> 3.15",
)

patch(
    libs / "OpenMesh" / "CMakeLists.txt",
    "cmake_minimum_required(VERSION 3.3.0 FATAL_ERROR)",
    "cmake_minimum_required(VERSION 3.15 FATAL_ERROR)",
    "cmake_minimum_required 3.3.0 -> 3.15",
)
