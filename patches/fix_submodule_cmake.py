"""Patch outdated CMake files in quadwild-bimdf submodule.

Fix 1: lemon sets CMP0048 to OLD, which newer CMake rejects.
Fix 2: json requires cmake_minimum_required 3.1, which is too old.
Fix 3: OpenMesh requires cmake_minimum_required 3.3.0, which is too old.
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
