"""
Realistic Field-Data Generator - synthetic test data for the example sites.
Produces physically-consistent synthetic ERT + MASW data matching generic
engineering-material groups. Useful for testing the full pipeline without
real field acquisitions.
"""
import os
import numpy as np
import pandas as pd


# Group-dependent parameters for synthetic signal generation.
GROUP_PARAMS = {
    'G1': {'rho_shallow': 800, 'rho_deep': 2500, 'vs_shallow': 420, 'vs_deep': 800},
    'G2': {'rho_shallow': 600, 'rho_deep': 1800, 'vs_shallow': 380, 'vs_deep': 650},
    'G3': {'rho_shallow': 150, 'rho_deep': 400, 'vs_shallow': 250, 'vs_deep': 380},
    'G5': {'rho_shallow': 50, 'rho_deep': 180, 'vs_shallow': 160, 'vs_deep': 300},
}


def generate_realistic_ert(group, n_a=16, max_a=32, n_x=10, noise_pct=5.0, seed=0):
    """Generate pseudo-section-style ERT data for one station."""
    rng = np.random.default_rng(seed)
    p = GROUP_PARAMS.get(group, GROUP_PARAMS['G3'])
    a_values = np.linspace(2, max_a, n_a)
    records = []
    for a in a_values:
        depth = a / 2
        # Smooth transition from shallow to deep rho based on pseudo-depth
        f = 1 / (1 + np.exp(-(depth - 10) / 3))
        rho_base = p['rho_shallow'] * (1 - f) + p['rho_deep'] * f
        for x_idx in range(n_x):
            x = x_idx * (100 - 2 * a) / max(1, n_x - 1) + a
            # Lateral variability
            lat = 1.0 + 0.15 * np.sin(x * 0.1)
            rho_a = rho_base * lat * (1 + rng.normal(0, noise_pct / 100))
            records.append({'electrode_a': a, 'x_center': x,
                            'rho_a': max(rho_a, 1.0)})
    return pd.DataFrame(records)


def generate_realistic_masw(group, n_t=4000, sr=2000, n_ch=24, dx=2.0, seed=0):
    """Generate synthetic MASW shot gather for one station."""
    rng = np.random.default_rng(seed)
    p = GROUP_PARAMS.get(group, GROUP_PARAMS['G3'])
    t = np.arange(n_t) / sr
    x = np.arange(n_ch) * dx
    # Dispersive surface wave: 4 modes with different vs
    traces = np.zeros((n_t, n_ch))
    # Fundamental Rayleigh
    for f_hz in np.linspace(5, 30, 12):
        depth = 0.5 * (p['vs_shallow'] + p['vs_deep']) / f_hz * 0.5
        f_depth = 1 / (1 + np.exp(-(depth - 15) / 5))
        vs_eff = p['vs_shallow'] * (1 - f_depth) + p['vs_deep'] * f_depth
        vr = vs_eff * 1.09
        amp = 1.0 / (1 + (f_hz / 15) ** 2)
        for i_ch in range(n_ch):
            delay = x[i_ch] / vr
            env = np.exp(-((t - 0.3 - delay) / 0.15) ** 2)
            traces[:, i_ch] += amp * env * np.sin(2 * np.pi * f_hz * (t - delay))
    # Add noise
    traces += rng.normal(0, 0.05, traces.shape)
    df = pd.DataFrame(traces, columns=[f'ch{i + 1:02d}' for i in range(n_ch)])
    return df


def generate_project_data(project):
    """Generate synthetic data for every site in the project."""
    ert_dir = project.ert_input_dir
    masw_dir = project.masw_input_dir
    os.makedirs(ert_dir, exist_ok=True)
    os.makedirs(masw_dir, exist_ok=True)
    for i, site in enumerate(project.sites):
        grp = site['group']
        ert_id = site['ert_id']
        mw_id = site.get('masw_id', ert_id.replace('ERT', 'MW'))
        # ERT
        df_ert = generate_realistic_ert(grp, seed=i * 7 + 1)
        df_ert.to_csv(os.path.join(ert_dir, f'{ert_id}.csv'), index=False)
        # MASW
        df_masw = generate_realistic_masw(grp, seed=i * 7 + 3)
        df_masw.to_csv(os.path.join(masw_dir, f'{mw_id}.csv'), index=False)
