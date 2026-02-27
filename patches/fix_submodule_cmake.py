"""Patch outdated CMake files in quadwild-bimdf submodule.

Fix 1: lemon sets CMP0048 to OLD, which newer CMake rejects.
Fix 2: json requires cmake_minimum_required 3.1, which is too old.
"""
from pathlib import Path

root = Path(__file__).resolve().parent.parent

# --- lemon: CMP0048 OLD → NEW ---
lemon_cmake = root / "quadwild-bimdf" / "libs" / "lemon" / "CMakeLists.txt"
content = lemon_cmake.read_text()
old = "CMAKE_POLICY(SET CMP0048 OLD)"
new = "CMAKE_POLICY(SET CMP0048 NEW)"
if old in content:
    lemon_cmake.write_text(content.replace(old, new))
    print(f"Patched {lemon_cmake}: CMP0048 OLD → NEW")
else:
    print(f"Already patched or changed: {lemon_cmake}")

# --- json: cmake_minimum_required 3.1 → 3.15 ---
json_cmake = root / "quadwild-bimdf" / "libs" / "json" / "CMakeLists.txt"
content = json_cmake.read_text()
old = "cmake_minimum_required(VERSION 3.1)"
new = "cmake_minimum_required(VERSION 3.15)"
if old in content:
    json_cmake.write_text(content.replace(old, new))
    print(f"Patched {json_cmake}: cmake_minimum_required 3.1 → 3.15")
else:
    print(f"Already patched or changed: {json_cmake}")
