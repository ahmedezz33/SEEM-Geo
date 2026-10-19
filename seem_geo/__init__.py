"""
SEEM Geo — Professional ERT & MASW Processing Suite
=====================================================
For engineering-geology site investigations: Electrical Resistivity Tomography
(Wenner-alpha) and Multichannel Analysis of Surface Waves processing, with
inversion, Vs30 computation, site classification, correlation framework, and
publication-ready outputs.

Open source · MIT License
"""
__version__ = '1.3.0'
__author__ = 'Ahmed'

from seem_geo.core.ert import process_ert_station, batch_ert
from seem_geo.core.masw import process_masw_station, batch_masw
from seem_geo.core.correlations import build_correlations
from seem_geo.core.fence import build_fence_diagrams
from seem_geo.core.project import SeemProject

# v1.2.1 — auto-load settings system (6-tab configurable dialog
# at ~/.seem_geo_settings.json) and runtime safe-fallback patches
# that connect those settings to ERT/MASW processing without
# breaking anything if the user hasn't configured them yet.
try:
    from seem_geo import settings  # applies matplotlib rcParams on import
except Exception as _e:
    import sys
    print(f'[seem_geo] settings module not loaded: {_e}', file=sys.stderr)

try:
    from seem_geo import core_patches  # safely wraps process_ert/masw_station
except Exception as _e:
    import sys
    print(f'[seem_geo] core_patches not loaded: {_e}', file=sys.stderr)

__all__ = [
    'SeemProject',
    'process_ert_station', 'batch_ert',
    'process_masw_station', 'batch_masw',
    'build_correlations', 'build_fence_diagrams',
]
