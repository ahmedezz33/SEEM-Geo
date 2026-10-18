"""
SeemProject - Project management & configuration.
Each .seemproj file is a JSON configuration that defines inputs, outputs,
and processing parameters for a complete geophysics campaign.
"""
import os
import json
from copy import deepcopy


DEFAULT_CONFIG = {
    "project": {
        "name": "Example Corridor Investigation",
        "description": "Example ERT + MASW geophysical survey along a 17-km linear corridor.",
        "author": "Project author",
        "institution": "the author's institution",
        "date": "2026",
        "version": "1.0",
    },
    "corridor": {
        "length_km": 17.0,
        "start_name": "West end",
        "end_name": "East end",
        "coordinate_system": "UTM (generic Zone 30N — fictional for demonstration)",
    },
    "paths": {
        "ert_input_dir": "data/ert_raw",
        "masw_input_dir": "data/masw_raw",
        "ert_output_dir": "outputs/ert",
        "masw_output_dir": "outputs/masw",
        "correlation_output_dir": "outputs/correlations",
        "fence_output_dir": "outputs/fence",
        "reports_dir": "outputs/reports",
        "bh_coordinates": "data/example_stations.csv",
    },
    "ert_acquisition": {
        "array": "Wenner-alpha",
        "n_electrodes": 48,
        "electrode_spacing_m": 2.0,
        "max_a_spacing_m": 32.0,
        "spread_length_m": 94.0,
    },
    "masw_acquisition": {
        "n_geophones": 24,
        "geophone_spacing_m": 2.0,
        "geophone_natural_freq_hz": 4.5,
        "spread_length_m": 46.0,
        "source": "sledgehammer, 10 kg, metal plate",
        "sample_rate_hz": 2000,
        "record_length_s": 2.0,
    },
    "processing": {
        "ert_inversion": {
            "nx_cells": 24,
            "nz_cells": 12,
            "max_depth_m": 30,
            "lambda_damping": 10.0,
            "n_iterations": 5,
        },
        "masw": {
            "sample_rate_hz": 2000,
            "geophone_spacing_m": 2.0,
            "f_min_hz": 4.0,
            "f_max_hz": 50.0,
            "v_min_ms": 100.0,
            "v_max_ms": 800.0,
            "pick_threshold": 0.85,
            "n_layers": 8,
            "max_depth_m": 30.0,
        },
    },
    "sites": [
        {"bh": "BH1", "ert_id": "ERT-01", "masw_id": "MW-01", "group": "G1",
         "ucs_mpa": 75.0, "rqd_pct": 85, "n60": 50, "chainage_km": 1.5},
        {"bh": "BH2", "ert_id": "ERT-02", "masw_id": "MW-02", "group": "G1",
         "ucs_mpa": 70.0, "rqd_pct": 80, "n60": 48, "chainage_km": 2.9},
        {"bh": "BH3", "ert_id": "ERT-03", "masw_id": "MW-03", "group": "G2",
         "ucs_mpa": 60.0, "rqd_pct": 72, "n60": 45, "chainage_km": 4.2},
        {"bh": "BH4", "ert_id": "ERT-04", "masw_id": "MW-04", "group": "G2",
         "ucs_mpa": 55.0, "rqd_pct": 68, "n60": 42, "chainage_km": 5.6},
        {"bh": "BH5", "ert_id": "ERT-05", "masw_id": "MW-05", "group": "G3",
         "ucs_mpa": 25.0, "rqd_pct": 45, "n60": 28, "chainage_km": 7.1},
        {"bh": "BH6", "ert_id": "ERT-06", "masw_id": "MW-06", "group": "G3",
         "ucs_mpa": 20.0, "rqd_pct": 40, "n60": 25, "chainage_km": 8.5},
        {"bh": "BH7", "ert_id": "ERT-07", "masw_id": "MW-07", "group": "G3",
         "ucs_mpa": 18.0, "rqd_pct": 35, "n60": 22, "chainage_km": 9.9},
        {"bh": "BH8", "ert_id": "ERT-08", "masw_id": "MW-08", "group": "G5",
         "ucs_mpa": 7.0, "rqd_pct": 20, "n60": 15, "chainage_km": 11.3},
        {"bh": "BH9", "ert_id": "ERT-09", "masw_id": "MW-09", "group": "G5",
         "ucs_mpa": 6.0, "rqd_pct": 18, "n60": 13, "chainage_km": 12.7},
        {"bh": "BH10", "ert_id": "ERT-10", "masw_id": "MW-10", "group": "G5",
         "ucs_mpa": 6.5, "rqd_pct": 22, "n60": 16, "chainage_km": 14.0},
        {"bh": "BH11", "ert_id": "ERT-11", "masw_id": "MW-11", "group": "G1",
         "ucs_mpa": 72.0, "rqd_pct": 82, "n60": 49, "chainage_km": 15.4},
        {"bh": "BH12", "ert_id": "ERT-12", "masw_id": "MW-12", "group": "G1",
         "ucs_mpa": 68.0, "rqd_pct": 78, "n60": 47, "chainage_km": 16.8},
    ],
    "groups": {
        "G1": {"name": "Group 1 (strong crystalline)", "color": "#2ECC40",
               "typical_vs": "500-900", "typical_ucs": "50-100", "class": "C"},
        "G2": {"name": "Group 2 (dense weathered rock)", "color": "#FF4136",
               "typical_vs": "400-650", "typical_ucs": "40-80", "class": "C"},
        "G3": {"name": "Group 3 (weak sedimentary)", "color": "#FFDC00",
               "typical_vs": "250-400", "typical_ucs": "10-30", "class": "D"},
        "G5": {"name": "Group 5 (residual / stiff soil)", "color": "#B10DC9",
               "typical_vs": "150-250", "typical_ucs": "2-10", "class": "D"},
    },
}


class SeemProject:
    """Project configuration & workspace manager."""

    def __init__(self, config=None, project_file=None):
        self.config = deepcopy(DEFAULT_CONFIG)
        if config is not None:
            self._merge(self.config, config)
        self.file = project_file
        self.root = os.path.dirname(os.path.abspath(project_file)) if project_file else os.getcwd()

    @staticmethod
    def _merge(base, override):
        for k, v in override.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                SeemProject._merge(base[k], v)
            else:
                base[k] = v

    @classmethod
    def load(cls, project_file):
        with open(project_file) as f:
            cfg = json.load(f)
        return cls(config=cfg, project_file=project_file)

    def save(self, path=None):
        path = path or self.file
        if path is None:
            raise ValueError("No project file set.")
        with open(path, 'w') as f:
            json.dump(self.config, f, indent=2)
        self.file = path
        self.root = os.path.dirname(os.path.abspath(path))
        return path

    @classmethod
    def init_default(cls, project_dir, name="New Project"):
        os.makedirs(project_dir, exist_ok=True)
        cfg = deepcopy(DEFAULT_CONFIG)
        cfg['project']['name'] = name
        project_file = os.path.join(project_dir, 'project.seemproj')
        with open(project_file, 'w') as f:
            json.dump(cfg, f, indent=2)
        proj = cls(config=cfg, project_file=project_file)
        proj._make_dirs()
        return proj

    def _make_dirs(self):
        for key in ('ert_input_dir', 'masw_input_dir', 'ert_output_dir',
                    'masw_output_dir', 'correlation_output_dir',
                    'fence_output_dir', 'reports_dir'):
            d = self.resolve_path(self.config['paths'][key])
            os.makedirs(d, exist_ok=True)

    def resolve_path(self, p):
        if os.path.isabs(p):
            return p
        return os.path.join(self.root, p)

    @property
    def sites(self):
        return self.config['sites']

    @property
    def groups(self):
        return self.config['groups']

    @property
    def ert_input_dir(self):
        return self.resolve_path(self.config['paths']['ert_input_dir'])

    @property
    def masw_input_dir(self):
        return self.resolve_path(self.config['paths']['masw_input_dir'])

    @property
    def ert_output_dir(self):
        return self.resolve_path(self.config['paths']['ert_output_dir'])

    @property
    def masw_output_dir(self):
        return self.resolve_path(self.config['paths']['masw_output_dir'])

    @property
    def correlation_output_dir(self):
        return self.resolve_path(self.config['paths']['correlation_output_dir'])

    @property
    def fence_output_dir(self):
        return self.resolve_path(self.config['paths']['fence_output_dir'])

    @property
    def reports_dir(self):
        return self.resolve_path(self.config['paths']['reports_dir'])

    def summary(self):
        return {
            'name': self.config['project']['name'],
            'n_sites': len(self.sites),
            'groups': list(self.groups.keys()),
            'root': self.root,
        }
