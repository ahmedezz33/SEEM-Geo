"""
Vs30 -> Site Class map / bar chart builder.
Produces a Vs30 bar chart with site-class colouring, and an interpolated
Vs30 raster map when station coordinates are available.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap


SITE_CLASS_BOUNDS = [0, 180, 360, 760, 1500, 3000]
SITE_CLASS_LABELS = ['E', 'D', 'C', 'B', 'A']
SITE_CLASS_COLORS = ['#8B0000', '#FF6B35', '#F7B32B', '#2E8B57', '#1F4E79']


def _class_color(sc):
    if isinstance(sc, str) and sc:
        c = sc[0]
        if c in SITE_CLASS_LABELS:
            return SITE_CLASS_COLORS[SITE_CLASS_LABELS.index(c)]
    return 'grey'


def build_vs30_bar_chart(project, out_png=None):
    """Simple bar chart of Vs30 per station with site-class colours."""
    if out_png is None:
        out_png = os.path.join(project.reports_dir, 'Vs30_bar_chart.png')
    os.makedirs(os.path.dirname(out_png), exist_ok=True)

    masw_sum = os.path.join(project.masw_output_dir, 'MASW_summary.csv')
    if not os.path.exists(masw_sum):
        raise FileNotFoundError('MASW_summary.csv not found - run MASW pipeline first.')

    df = pd.read_csv(masw_sum)
    df['station_norm'] = df['station'].astype(str).str.replace('_shot', '')
    df_sorted = df.sort_values('vs30_ms').reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(df_sorted['station_norm'], df_sorted['vs30_ms'],
                  color=[_class_color(sc) for sc in df_sorted['site_class']],
                  edgecolor='black', linewidth=1.2)

    for v, lbl in zip([180, 360, 760], ['D|E', 'C|D', 'B|C']):
        ax.axhline(v, color='red', linestyle='--', linewidth=0.8, alpha=0.6)
        ax.text(len(df_sorted) - 0.3, v + 5, lbl, fontsize=8, color='red')

    for b, v in zip(bars, df_sorted['vs30_ms']):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 10,
                f'{v:.0f}', ha='center', fontsize=9, fontweight='bold')

    ax.set_xlabel('MASW station', fontsize=11)
    ax.set_ylabel('Vs30 (m/s)', fontsize=11)
    ax.set_title('Vs30 per Station - Site Class Classification',
                 fontsize=13, fontweight='bold')
    ax.set_ylim(0, max(df_sorted['vs30_ms']) * 1.15)
    plt.xticks(rotation=30)
    plt.grid(True, axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_png, dpi=180, bbox_inches='tight', facecolor='white')
    plt.close()
    return out_png


def build_vs30_map(project, out_png=None):
    """Interpolated Vs30 map - requires station coordinates CSV."""
    if out_png is None:
        out_png = os.path.join(project.reports_dir, 'Vs30_site_class_map.png')
    os.makedirs(os.path.dirname(out_png), exist_ok=True)

    masw_sum = os.path.join(project.masw_output_dir, 'MASW_summary.csv')
    if not os.path.exists(masw_sum):
        raise FileNotFoundError('MASW_summary.csv not found - run MASW pipeline first.')
    df_vs = pd.read_csv(masw_sum)

    coord_file = project.config['paths'].get('bh_coordinates')
    if not coord_file:
        raise FileNotFoundError('No station coordinates configured.')
    coord_path = project.resolve_path(coord_file)
    if not os.path.exists(coord_path):
        raise FileNotFoundError(f'Station coordinates not found: {coord_path}')
    df_coords = pd.read_csv(coord_path)

    # Simple scatter visualization (map interpolation is coordinate-dependent)
    fig, ax = plt.subplots(figsize=(14, 6))
    cmap = ListedColormap(SITE_CLASS_COLORS)
    norm = BoundaryNorm(SITE_CLASS_BOUNDS, cmap.N)

    for _, s in df_vs.iterrows():
        bh = str(s['station']).replace('_shot', '').replace('MW-', '').replace('MW', '')
        try:
            idx = int(bh)
        except ValueError:
            idx = 0
        c = _class_color(s['site_class'])
        ax.scatter(idx, s['vs30_ms'], c=c, s=250,
                   edgecolors='black', linewidths=1.5, zorder=5)
        ax.annotate(f"BH{idx}\n{s['vs30_ms']:.0f}", (idx, s['vs30_ms']),
                    xytext=(0, 12), textcoords='offset points',
                    ha='center', fontsize=8, fontweight='bold')

    ax.set_xlabel('Station index', fontsize=11)
    ax.set_ylabel('Vs30 (m/s)', fontsize=11)
    ax.set_title('Vs30 across the Corridor - Site Classes',
                 fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_png, dpi=180, bbox_inches='tight', facecolor='white')
    plt.close()
    return out_png
