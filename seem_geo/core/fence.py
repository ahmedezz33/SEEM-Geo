"""Fence diagram builder - ERT ribbon + MASW stick model along corridor."""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.patches import Rectangle


GROUP_COLORS = {'G1': '#2ECC40', 'G2': '#FF4136', 'G3': '#FFDC00', 'G5': '#B10DC9'}


def build_ert_fence(project, out_png=None):
    """Combined ERT fence diagram showing all stations along chainage."""
    if out_png is None:
        out_png = os.path.join(project.fence_output_dir, 'ERT_fence_diagram.png')

    sites = project.sites
    n_sites = len(sites)
    fig, axes = plt.subplots(1, n_sites, figsize=(2.5 * n_sites, 6),
                             sharey=True, gridspec_kw={'wspace': 0.05})
    if n_sites == 1:
        axes = [axes]

    for ax, site in zip(axes, sites):
        bh = site['bh']
        grp = site['group']
        chainage = site.get('chainage_km', 0)
        model_csv = os.path.join(project.ert_output_dir, f"{site['ert_id']}_model.csv")
        if not os.path.exists(model_csv):
            ax.text(0.5, 0.5, 'No data', ha='center', va='center',
                    transform=ax.transAxes, fontsize=8)
            ax.set_title(f'{bh}\n{chainage:.1f} km', fontsize=9, fontweight='bold',
                         color=GROUP_COLORS.get(grp, 'black'))
            continue
        df = pd.read_csv(model_csv)
        pivot = df.pivot(index='z_m', columns='x_m', values='rho_ohm_m').sort_index()
        X, Z = np.meshgrid(pivot.columns, pivot.index)
        vmin = max(df['rho_ohm_m'].min(), 1)
        vmax = df['rho_ohm_m'].max()
        im = ax.pcolormesh(X, Z, pivot.values, cmap='turbo',
                           norm=LogNorm(vmin=vmin, vmax=vmax), shading='auto')
        ax.invert_yaxis()
        ax.set_title(f'{bh} ({grp})\n{chainage:.1f} km',
                     fontsize=9, fontweight='bold',
                     color=GROUP_COLORS.get(grp, 'black'))
        ax.set_xticks([])
    axes[0].set_ylabel('Depth (m)', fontsize=11)
    plt.suptitle('ERT Fence Diagram - Inverted True-Resistivity Sections along Corridor',
                 fontsize=13, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(out_png, dpi=180, bbox_inches='tight', facecolor='white')
    plt.close()
    return out_png


def build_masw_fence(project, out_png=None):
    """Combined MASW Vs-profile fence diagram."""
    if out_png is None:
        out_png = os.path.join(project.fence_output_dir, 'MASW_fence_diagram.png')

    sites = project.sites
    n_sites = len(sites)
    fig, axes = plt.subplots(1, n_sites, figsize=(2.0 * n_sites, 7),
                             sharey=True, gridspec_kw={'wspace': 0.05})
    if n_sites == 1:
        axes = [axes]

    for ax, site in zip(axes, sites):
        bh = site['bh']
        grp = site['group']
        chainage = site.get('chainage_km', 0)
        mw_id = site.get('masw_id', site['ert_id'].replace('ERT', 'MW'))
        vs_csv = os.path.join(project.masw_output_dir, f'{mw_id}_vs_profile.csv')
        if not os.path.exists(vs_csv):
            ax.text(0.5, 0.5, 'No data', ha='center', va='center',
                    transform=ax.transAxes, fontsize=8)
            ax.set_title(f'{bh}\n{chainage:.1f} km', fontsize=8)
            continue
        df = pd.read_csv(vs_csv)
        for _, row in df.iterrows():
            ax.fill_betweenx([row['z_top_m'], row['z_bot_m']], 0, row['vs_ms'],
                             facecolor=GROUP_COLORS.get(grp, 'steelblue'),
                             edgecolor='black', linewidth=0.5, alpha=0.85)
        ax.set_xlim(0, 900)
        ax.set_title(f'{bh}\n{chainage:.1f} km',
                     fontsize=8, fontweight='bold',
                     color=GROUP_COLORS.get(grp, 'black'))
        ax.invert_yaxis()
        ax.set_xticks([0, 300, 600, 900])
        ax.tick_params(axis='x', labelsize=7)
    axes[0].set_ylabel('Depth (m)', fontsize=11)
    plt.suptitle('MASW Fence Diagram - Vs Profiles along Corridor',
                 fontsize=13, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(out_png, dpi=180, bbox_inches='tight', facecolor='white')
    plt.close()
    return out_png


def build_corridor_ribbon(project, out_png=None):
    """Chainage-vs-depth ribbon showing group transitions."""
    if out_png is None:
        out_png = os.path.join(project.fence_output_dir, 'Corridor_ribbon.png')

    sites = sorted(project.sites, key=lambda s: s.get('chainage_km', 0))
    fig, ax = plt.subplots(figsize=(16, 5))
    chainages = [s.get('chainage_km', 0) for s in sites]
    for i, s in enumerate(sites):
        x_start = chainages[i] - 0.6 if i == 0 else (chainages[i - 1] + chainages[i]) / 2
        x_end = chainages[i] + 0.6 if i == len(sites) - 1 else (chainages[i] + chainages[i + 1]) / 2
        ax.add_patch(Rectangle((x_start, 0), x_end - x_start, 30,
                               facecolor=GROUP_COLORS.get(s['group'], 'grey'),
                               edgecolor='black', linewidth=0.6, alpha=0.85))
        ax.text(chainages[i], 1.5, s['bh'], ha='center', fontsize=9,
                fontweight='bold', rotation=0)
    ax.set_xlim(min(chainages) - 1, max(chainages) + 1)
    ax.set_ylim(30, 0)
    ax.set_xlabel('Chainage (km)', fontsize=11)
    ax.set_ylabel('Depth (m)', fontsize=11)
    ax.set_title('Corridor Lithology Ribbon - Group Transitions',
                 fontsize=13, fontweight='bold')
    # Legend
    from matplotlib.patches import Patch
    legend_elems = [Patch(facecolor=c, edgecolor='black', label=g)
                    for g, c in GROUP_COLORS.items()
                    if g in set(s['group'] for s in sites)]
    ax.legend(handles=legend_elems, loc='upper right', fontsize=9, framealpha=0.9)
    plt.tight_layout()
    plt.savefig(out_png, dpi=180, bbox_inches='tight', facecolor='white')
    plt.close()
    return out_png


def build_fence_diagrams(project):
    """Build all fence outputs."""
    os.makedirs(project.fence_output_dir, exist_ok=True)
    outputs = {
        'ert_fence': build_ert_fence(project),
        'masw_fence': build_masw_fence(project),
        'corridor_ribbon': build_corridor_ribbon(project),
    }
    return outputs
