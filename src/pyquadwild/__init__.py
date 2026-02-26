# SPDX-License-Identifier: GPL-3.0-or-later
"""
pyquadwild — Python bindings for QuadWild BiMDF quad-dominant remeshing.

Functions
---------
quadwild_remesh
    Full quad-dominant remeshing pipeline (field → trace → quadrangulate).
"""

from pyquadwild.quadwild import quadwild_remesh

__version__ = "0.1.0"
__all__ = ["quadwild_remesh"]
