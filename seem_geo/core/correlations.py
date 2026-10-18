"""Correlation framework builder - rho vs RQD, Vs vs N60, Vs vs RQD, Vs vs UCS."""
import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats


GROUP_COLORS = {'G1': '#2ECC40', 'G2': '#FF4136', 'G3': '#FFDC00', 'G5': '#B10DC9'}


def fit_linear(x, y):
    """Linear regression with full statistics."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) < 3:
        return {'slope': 0, 'intercept': 0, 'r2': 0, 'p': 1,
                'n': len(x), 'df': 0, 'ci_slope': (0, 0)}
    slope, intercept, r, p, se = stats.linregress(x, y)
    n = len(x)
    df = n - 2
    t_crit = stats.t.ppf(0.975, df)
    ci_slope = (slope - t_crit * se, slope + t_crit * se)
    return {
        'slope': float(slope),
        'intercept': float(intercept),
        'r2': float(r ** 2),
        'r': float(r),
        'p': float(p),
        'se': float(se),
        'n': n,
        'df': df,
        'ci_slope': (float(ci_slope[0]), float(ci_slope[1])),
    }


def plot_correlation(df_pts, x_col, y_col, title, out_png, xlabel=None, ylabel=None):
    fig, ax = plt.subplots(figsize=(8, 6))
    for g in df_pts['group'].unique():
        sub = df_pts[df_pts['group'] == g]
        ax.scatter(sub[x_col], sub[y_col],
                   c=GROUP_COLORS.get(g, 'grey'),
                   s=110, edgecolors='black', linewidths=1.2,
                   label=g, zorder=5)
    stats_dict = fit_linear(df_pts[x_col], df_pts[y_col])
    xs = np.linspace(df_pts[x_col].min(), df_pts[x_col].max(), 100)
    ys = stats_dict['slope'] * xs + stats_dict['intercept']
    ax.plot(xs, ys, 'k--', linewidth=1.5, alpha=0.7,
            label=f"y = {stats_dict['slope']:.3f}x + {stats_dict['intercept']:.1f}")
    ax.set_xlabel(xlabel or x_col, fontsize=11)
    ax.set_ylabel(ylabel or y_col, fontsize=11)
    ax.set_title(f'{title}\nR^2 = {stats_dict["r2"]:.3f}, p = {stats_dict["p"]:.3e}, n = {stats_dict["n"]}',
                 fontsize=12, fontweight='bold')
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_png, dpi=180, bbox_inches='tight', facecolor='white')
    plt.close()
    return stats_dict


def build_correlations(project):
    """Build the 8-correlation framework from ERT, MASW, and borehole data."""
    out_dir = project.correlation_output_dir
    os.makedirs(out_dir, exist_ok=True)

    # Gather data
    ert_sum = os.path.join(project.ert_output_dir, 'ERT_summary.csv')
    masw_sum = os.path.join(project.masw_output_dir, 'MASW_summary.csv')
    df_ert = pd.read_csv(ert_sum) if os.path.exists(ert_sum) else pd.DataFrame()
    df_masw = pd.read_csv(masw_sum) if os.path.exists(masw_sum) else pd.DataFrame()

    rows = []
    for site in project.sites:
        bh = site['bh']
        grp = site['group']
        rho_row = df_ert[df_ert['bh'] == bh]
        vs_row = df_masw[df_masw['bh'] == bh]
        rho_mean = float(rho_row['rho_model_mean'].iloc[0]) if len(rho_row) else np.nan
        vs30 = float(vs_row['vs30_ms'].iloc[0]) if len(vs_row) else np.nan
        rows.append({
            'bh': bh,
            'group': grp,
            'rho_mean': rho_mean,
            'vs30': vs30,
            'ucs': site.get('ucs_mpa', np.nan),
            'rqd': site.get('rqd_pct', np.nan),
            'n60': site.get('n60', np.nan),
        })
    df = pd.DataFrame(rows).dropna(subset=['rho_mean', 'vs30'])
    df.to_csv(os.path.join(out_dir, 'master_correlation_table.csv'), index=False)

    # Build the four main correlations
    correlations = [
        ('rho_mean', 'rqd', 'rho (Ohm.m)', 'RQD (%)', 'rho vs RQD'),
        ('vs30', 'n60', 'Vs30 (m/s)', 'N60 (blows/300mm)', 'Vs30 vs N60'),
        ('vs30', 'rqd', 'Vs30 (m/s)', 'RQD (%)', 'Vs30 vs RQD'),
        ('vs30', 'ucs', 'Vs30 (m/s)', 'UCS (MPa)', 'Vs30 vs UCS'),
    ]
    all_stats = {}
    for x_col, y_col, xlab, ylab, title in correlations:
        sub = df.dropna(subset=[x_col, y_col])
        if len(sub) < 3:
            continue
        out_png = os.path.join(out_dir, f'corr_{x_col}_vs_{y_col}.png')
        s = plot_correlation(sub, x_col, y_col, title, out_png, xlab, ylab)
        all_stats[f'{x_col}_vs_{y_col}'] = s

    with open(os.path.join(out_dir, 'correlation_stats.json'), 'w') as f:
        json.dump(all_stats, f, indent=2)
    return all_stats
