"""MASW (Multichannel Analysis of Surface Waves) processing module."""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import detrend
from scipy.signal.windows import tukey


def read_shot_csv(path, sr=2000, dx=2.0):
    """CSV: columns = channel traces, rows = time samples."""
    df = pd.read_csv(path)
    traces = df.values.astype(float)
    n_t, n_ch = traces.shape
    t = np.arange(n_t) / sr
    x = np.arange(n_ch) * dx
    return t, x, traces


def read_masw_csv(path, sr_hz=2000, dx_m=2.0):
    return read_shot_csv(path, sr=sr_hz, dx=dx_m)


def slant_stack_fv(traces, t, x, f_min=4.0, f_max=50.0, v_min=100.0, v_max=800.0,
                   n_f=200, n_v=240):
    """f-v slant-stack transform (surface-wave dispersion imaging)."""
    n_t, n_ch = traces.shape
    dt = t[1] - t[0]
    freqs = np.fft.rfftfreq(n_t, dt)
    taper = tukey(n_t, 0.1)
    traces_tap = detrend(traces, axis=0) * taper[:, None]
    U = np.fft.rfft(traces_tap, axis=0)
    f_axis = np.linspace(f_min, f_max, n_f)
    v_axis = np.linspace(v_min, v_max, n_v)
    FV = np.zeros((n_f, n_v))
    for i_f, f in enumerate(f_axis):
        idx = np.argmin(np.abs(freqs - f))
        U_f = U[idx, :]
        for i_v, v in enumerate(v_axis):
            k = 2 * np.pi * f / v
            phase = np.exp(1j * k * x)
            s = np.sum(U_f * phase)
            FV[i_f, i_v] = np.abs(s)
    for i_f in range(n_f):
        m = FV[i_f, :].max()
        if m > 0:
            FV[i_f, :] /= m
    return f_axis, v_axis, FV


def auto_pick_dispersion(f_axis, v_axis, FV, threshold=0.85, trim=True,
                           max_rel_jump=0.20, min_run=6):
    """Pick fundamental-mode dispersion by max-energy ridge.

    Uses quadratic (parabolic) peak-fitting around the argmax to get
    sub-grid velocity precision (~0.1 m/s instead of the v_axis step).
    This matters when two surveys sit in similar material: the raw argmax
    would snap both to the same v-bin and hide genuine field variability.

    When ``trim=True`` (default) the picks are passed through
    :func:`trim_picks_to_coherent_mode` which keeps only the longest coherent
    run of the ridge — any pick whose velocity jumps by more than
    ``max_rel_jump`` from its neighbor is treated as a higher-mode or
    noise contaminant and dropped.  ``min_run`` is the minimum number of
    consecutive-frequency picks that constitutes a valid ridge segment.
    """
    picks = []
    n_v = len(v_axis)
    dv = (v_axis[-1] - v_axis[0]) / (n_v - 1) if n_v > 1 else 1.0
    for i_f, f in enumerate(f_axis):
        row = FV[i_f, :]
        i_max = int(np.argmax(row))
        peak = float(row[i_max])
        if peak < threshold:
            continue
        # Parabolic sub-grid refinement when the peak is interior
        if 0 < i_max < n_v - 1:
            y_m, y_0, y_p = float(row[i_max - 1]), peak, float(row[i_max + 1])
            denom = (y_m - 2 * y_0 + y_p)
            if abs(denom) > 1e-12:
                shift = 0.5 * (y_m - y_p) / denom  # in units of grid steps
                shift = max(-1.0, min(1.0, shift))  # clamp
                v_pick = float(v_axis[i_max] + shift * dv)
            else:
                v_pick = float(v_axis[i_max])
        else:
            v_pick = float(v_axis[i_max])
        picks.append((f, v_pick))
    picks = np.array(picks)
    if trim and len(picks) >= min_run:
        picks = trim_picks_to_coherent_mode(
            picks, max_rel_jump=max_rel_jump, min_run=min_run)
    return picks


def trim_picks_to_coherent_mode(picks, max_rel_jump=0.20, min_run=6):
    """Keep only the longest coherent run of the dispersion ridge.

    A pick is considered part of the coherent fundamental mode when its
    phase velocity does not jump by more than ``max_rel_jump`` (fractional)
    from the previous pick at an adjacent frequency.  Picks after a big
    jump are usually higher-mode leakage or noise and are dropped.
    Returns the longest run of such consecutive picks that is at least
    ``min_run`` samples long; if no segment qualifies, returns the input
    unchanged.

    This fixes the common problem where a MASW spread's response rolls
    off above a certain frequency (often 25-40 Hz for shallow surveys)
    and the picker starts chasing higher-mode or ambient-noise ridges.
    """
    if len(picks) < min_run:
        return picks
    f = picks[:, 0]
    v = picks[:, 1]
    order = np.argsort(f)
    f = f[order]; v = v[order]

    # Walk through picks; break the chain whenever v changes too much
    segments = [[0]]
    for i in range(1, len(f)):
        rel = abs(v[i] - v[i - 1]) / max(v[i - 1], 1.0)
        if rel <= max_rel_jump:
            segments[-1].append(i)
        else:
            segments.append([i])
    # Choose the longest segment that meets min_run
    best = max(segments, key=len)
    if len(best) < min_run:
        return np.column_stack([f, v])  # nothing coherent — return sorted
    idx = np.array(best, dtype=int)
    return np.column_stack([f[idx], v[idx]])


def plot_dispersion_image(f_axis, v_axis, FV, picks, out_png, station_id="MW-??",
                           bh=None, group=None, group_name=None,
                           crop_to_picks=True, f_margin=0.3, v_margin=0.5):
    """Publication-quality f-v dispersion image with smooth interpolation.

    When ``crop_to_picks=True`` (default) the frequency and velocity axes are
    cropped to the picked region plus a configurable margin (``f_margin`` and
    ``v_margin``, both fractional).  This hides the noise outside the usable
    band and focuses the reader on the fundamental mode ridge.  Pass
    ``crop_to_picks=False`` to see the full raw image.
    """
    fig, ax = plt.subplots(figsize=(11, 6.5), facecolor='white')
    F, V = np.meshgrid(f_axis, v_axis, indexing='ij')
    # Gouraud shading gives bilinear interpolation across cells, so the image
    # reads as a continuous energy field rather than discrete bins.  Lower
    # vmin raises the floor so weak-energy regions do not dominate the plot
    # with chaotic color.
    im = ax.pcolormesh(F, V, FV, cmap='turbo', shading='gouraud',
                        vmin=0.15, vmax=1.0)
    if len(picks) > 0:
        ax.plot(picks[:, 0], picks[:, 1], 'wo-', markersize=5,
                markeredgecolor='black', linewidth=1.3,
                label='Fundamental-mode picks')
        ax.legend(loc='upper right', fontsize=10, framealpha=0.9,
                   edgecolor='black')

    # Crop axes to the picked region plus margin, so the noisy out-of-band
    # region does not dominate the figure.  Only crops when we have picks.
    if crop_to_picks and len(picks) > 0:
        f_lo, f_hi = float(picks[:, 0].min()), float(picks[:, 0].max())
        v_lo, v_hi = float(picks[:, 1].min()), float(picks[:, 1].max())
        f_pad = (f_hi - f_lo) * f_margin
        v_pad = (v_hi - v_lo) * v_margin
        ax.set_xlim(max(float(f_axis[0]), f_lo - f_pad),
                     min(float(f_axis[-1]), f_hi + f_pad))
        ax.set_ylim(max(float(v_axis[0]), v_lo - v_pad),
                     min(float(v_axis[-1]), v_hi + v_pad))

    ax.set_xlabel('Frequency (Hz)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Phase velocity (m/s)', fontsize=12, fontweight='bold')
    title_parts = [station_id]
    if bh:         title_parts.append(bh)
    if group_name: title_parts.append(group_name)
    elif group:    title_parts.append(group)
    ax.set_title('  |  '.join(title_parts) + '\nf-v Dispersion Image',
                  fontsize=12, fontweight='bold', pad=12)
    cbar = plt.colorbar(im, ax=ax, label='Normalized energy', pad=0.015)
    cbar.ax.tick_params(labelsize=9)
    ax.grid(True, alpha=0.25, linestyle=':', color='white')
    plt.tight_layout()
    plt.savefig(out_png, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    return out_png


def dispersion_to_vs_profile(picks, n_layers=12, max_depth=30.0, clip_to_resolved=True):
    """Convert picks to a physically-plausible Vs(z) profile.

    Uses a half-wavelength depth transform (z ≈ Vr/(2.5·f)) and the Rayleigh→
    shear conversion Vs ≈ 1.1·Vr for a Poisson ratio around 0.3, then applies
    Gaussian smoothing and a soft monotonic-increase constraint so the output
    reflects a layered earth whose stiffness grows with depth (rather than the
    zigzag that raw depth-bin averaging produces when picks cluster unevenly).

    When ``clip_to_resolved=True`` (default) the output depth is clipped to the
    data-support depth z_max = v(f_min) / (2.5·f_min), i.e. the deepest point
    actually probed by the lowest-frequency pick. This avoids a misleading
    flat tail of extrapolated values below the resolution limit. Pass
    ``clip_to_resolved=False`` for the legacy behaviour (extends to max_depth).
    """
    if len(picks) < 3:
        return np.array([0, max_depth]), np.array([250.0])

    f = picks[:, 0].astype(float)
    v = picks[:, 1].astype(float)
    mask = (f > 0) & (v > 0)
    f, v = f[mask], v[mask]
    if len(v) < 3:
        return np.array([0, max_depth]), np.array([250.0])

    # Depth transform and Rayleigh→Vs conversion
    z_r = v / (2.5 * f)
    vs_r = 1.1 * v

    # Keep picks within the target depth window
    keep = z_r <= max_depth * 1.2
    z_r, vs_r = z_r[keep], vs_r[keep]
    if len(z_r) < 3:
        return np.array([0, max_depth]), np.array([250.0])

    order = np.argsort(z_r)
    z_r, vs_r = z_r[order], vs_r[order]

    # Clip the output depth to the data-support depth (lowest-frequency pick)
    if clip_to_resolved:
        f_min = float(f.min())
        v_at_fmin = float(v[f.argmin()])
        z_resolved = v_at_fmin / (2.5 * f_min)
        max_depth = min(max_depth, z_resolved)

    # Fine grid, interpolate, smooth
    z_grid = np.linspace(0.5, max_depth, 200)
    vs_grid = np.interp(z_grid, z_r, vs_r)
    try:
        from scipy.ndimage import gaussian_filter1d
        vs_grid = gaussian_filter1d(vs_grid, sigma=10)
    except ImportError:
        for _ in range(20):
            vs_grid[1:-1] = (vs_grid[:-2] + 2 * vs_grid[1:-1] + vs_grid[2:]) / 4

    # Soft monotonic constraint — allow small (5%) dips but keep the trend
    for i in range(1, len(vs_grid)):
        if vs_grid[i] < vs_grid[i - 1] * 0.95:
            vs_grid[i] = vs_grid[i - 1] * 0.98
    cummax = np.maximum.accumulate(vs_grid * 0.98)
    vs_grid = 0.7 * vs_grid + 0.3 * cummax

    # Bin into output layers
    z_bounds = np.linspace(0, max_depth, n_layers + 1)
    vs_layers = np.zeros(n_layers)
    for i in range(n_layers):
        m = (z_grid >= z_bounds[i]) & (z_grid < z_bounds[i + 1])
        if m.sum() > 0:
            vs_layers[i] = float(np.mean(vs_grid[m]))
        else:
            vs_layers[i] = vs_layers[i - 1] if i > 0 else 250.0
    return z_bounds, vs_layers


def compute_vs30(z_bounds, vs_layers):
    """Travel-time weighted average over top 30 m.

    When the profile is shorter than 30 m (because the picks did not resolve
    down to that depth), the integral below the deepest resolved layer is
    completed using that layer's Vs as a flat extrapolation. This is the
    standard engineering convention for site-class determination when MASW
    does not reach the full 30 m window; the alternative (ignoring the
    unresolved portion) biases Vs30 toward the softer surface materials and
    under-classifies the site.
    """
    if len(vs_layers) == 0:
        return 0.0
    t_total = 0.0
    z_total = 0.0
    last_vs = None
    for i, vs in enumerate(vs_layers):
        z_top = z_bounds[i]
        z_bot = z_bounds[i + 1]
        if z_top >= 30:
            break
        dz = min(z_bot, 30) - z_top
        if dz > 0 and vs > 0:
            t_total += dz / vs
            z_total += dz
            last_vs = vs
    # Extend to 30 m with the deepest resolved Vs if we fell short
    if z_total > 0 and z_total < 30 and last_vs:
        remainder = 30 - z_total
        t_total += remainder / last_vs
        z_total = 30.0
    if t_total == 0:
        return 0.0
    return z_total / t_total


def site_class_from_vs30(vs30):
    """Generic site-classification scheme (A/B/C/D/E)."""
    if vs30 >= 1500:
        return 'A - Hard rock'
    if vs30 >= 760:
        return 'B - Rock'
    if vs30 >= 360:
        return 'C - Very dense soil / soft rock'
    if vs30 >= 180:
        return 'D - Stiff soil'
    return 'E - Soft soil'


# NEHRP / IBC Site Class bands used in the Vs profile plot:
# (Vs30_lo, Vs30_hi, letter, fill_color, descriptive_name)
_SITE_CLASS_BANDS = [
    (0,    180,  'E', '#FEE2E2', 'Soft soil'),
    (180,  360,  'D', '#FEF3C7', 'Stiff soil'),
    (360,  760,  'C', '#DBEAFE', 'Very dense soil / soft rock'),
    (760,  1500, 'B', '#D1FAE5', 'Rock'),
    (1500, 5000, 'A', '#E5E7EB', 'Hard rock'),
]


def plot_vs_profile(z_bounds, vs_layers, out_png, station_id="MW-??",
                     vs30=None, bh=None, group=None, group_color=None,
                     group_name=None):
    """Publication-quality Vs(z) step plot.

    Draws NEHRP/IBC Site Class color bands as the background, the Vs(z) profile
    as a step line filled with the group color, per-layer value labels, and the
    Vs30 reference line.  Extra annotation arguments are optional for backward
    compatibility.
    """
    fig, ax = plt.subplots(figsize=(8, 10), facecolor='white')

    xmax = max(float(np.max(vs_layers)) * 1.3, 800.0)

    # Site Class color bands
    for lo, hi, cls, color, _ in _SITE_CLASS_BANDS:
        if lo >= xmax:
            break
        ax.axvspan(lo, min(hi, xmax), color=color, alpha=0.35, zorder=0)
        if lo < xmax * 0.9:
            ax.text(lo + 10, max(z_bounds[-1] - 0.4, 0.1), f'Class {cls}',
                     fontsize=8, color='#374151', fontweight='bold',
                     va='bottom', zorder=1)

    # Vs(z) step line + group-color fill
    z_plot = np.repeat(z_bounds, 2)[1:-1]
    vs_plot = np.repeat(vs_layers, 2)
    fill_c = group_color or '#4682B4'
    ax.plot(vs_plot, z_plot, '-', color='#1F2937',
             linewidth=2.5, zorder=3, label='Vs(z)')
    ax.fill_betweenx(z_plot, 0, vs_plot, alpha=0.3,
                     color=fill_c, zorder=2)

    # Per-layer value labels
    for i, vs in enumerate(vs_layers):
        z_mid = (z_bounds[i] + z_bounds[i + 1]) / 2
        ax.annotate(f'{vs:.0f}', (vs, z_mid),
                     xytext=(8, 0), textcoords='offset points',
                     fontsize=8.5, color='#1F2937', va='center', ha='left')

    # Vs30 reference
    if vs30 is not None:
        ax.axvline(vs30, color='red', linestyle='--', linewidth=1.5,
                    alpha=0.85, zorder=4, label=f'Vs30 = {vs30:.0f} m/s')

    # 30 m reference line and depth-of-resolution marker
    resolved_depth = float(z_bounds[-1])
    if resolved_depth < 30:
        # Mark the end of resolved data within the plot, and note that
        # Vs30 was completed using flat extrapolation to 30 m.
        ax.axhline(resolved_depth, color='orange', linestyle='--',
                    linewidth=1.2, alpha=0.7)
        ax.text(xmax * 0.98, resolved_depth - 0.3,
                 f'Max resolved depth = {resolved_depth:.1f} m\n'
                 f'Vs30 completed with flat Vs below',
                 color='#B45309', fontsize=8, va='bottom', ha='right',
                 fontweight='bold',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                            alpha=0.85, edgecolor='#B45309'))
    else:
        ax.axhline(30, color='red', linestyle=':', linewidth=1.2, alpha=0.7)
        ax.text(xmax * 0.02, 30.4, 'Vs30 depth (30 m)', color='red',
                 fontsize=9, va='top', fontweight='bold')

    ax.set_xlim(0, xmax)
    # Always plot to at least 15 m so the Site Class bands context is visible,
    # but never beyond the data-resolved depth
    plot_ymax = max(resolved_depth + 1, 15)
    ax.set_ylim(plot_ymax, 0)   # inverted depth
    ax.set_xlabel('Shear-wave velocity Vs (m/s)',
                   fontsize=12, fontweight='bold')
    ax.set_ylabel('Depth (m)', fontsize=12, fontweight='bold')

    # Rich title
    title_parts = [station_id]
    if bh:         title_parts.append(bh)
    if group_name: title_parts.append(group_name)
    elif group:    title_parts.append(group)
    subtitle = ''
    if vs30 is not None:
        sc = site_class_from_vs30(vs30)
        subtitle = f'\nVs30 = {vs30:.0f} m/s  |  Site Class {sc}'
    ax.set_title('  |  '.join(title_parts) + subtitle,
                  fontsize=12, fontweight='bold', pad=12)
    ax.legend(loc='lower left', fontsize=10,
               framealpha=0.9, edgecolor='black')
    ax.grid(True, alpha=0.4, linestyle=':', zorder=1)
    plt.tight_layout()
    plt.savefig(out_png, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    return out_png


def process_masw_station(input_path, out_dir, station_id=None,
                         sr_hz=2000, dx_m=2.0, verbose=False):
    station_id = station_id or os.path.splitext(os.path.basename(input_path))[0]
    t, x, traces = read_masw_csv(input_path, sr_hz=sr_hz, dx_m=dx_m)
    f_axis, v_axis, FV = slant_stack_fv(traces, t, x)
    picks = auto_pick_dispersion(f_axis, v_axis, FV)
    disp_png = os.path.join(out_dir, f'{station_id}_dispersion.png')
    plot_dispersion_image(f_axis, v_axis, FV, picks, disp_png, station_id)
    if len(picks) > 0:
        pd.DataFrame(picks, columns=['freq_hz', 'phase_vel_ms']).to_csv(
            os.path.join(out_dir, f'{station_id}_picks.csv'), index=False)
    z_bounds, vs_layers = dispersion_to_vs_profile(picks)
    vs30 = compute_vs30(z_bounds, vs_layers)
    site_class = site_class_from_vs30(vs30)
    vs_png = os.path.join(out_dir, f'{station_id}_vs_profile.png')
    plot_vs_profile(z_bounds, vs_layers, vs_png, station_id, vs30)
    if len(z_bounds) > 1:
        pd.DataFrame({
            'z_top_m': z_bounds[:-1],
            'z_bot_m': z_bounds[1:],
            'vs_ms': vs_layers,
        }).to_csv(os.path.join(out_dir, f'{station_id}_vs_profile.csv'), index=False)
    return {
        'station': station_id,
        'n_picks': len(picks),
        'vs30_ms': float(vs30),
        'site_class': site_class,
    }


def batch_masw(project, progress_callback=None, verbose=False):
    results = []
    sites = project.sites
    sr = project.config['processing']['masw'].get('sample_rate_hz', 2000)
    dx = project.config['processing']['masw'].get('geophone_spacing_m', 2.0)
    for i, site in enumerate(sites):
        mw_id = site.get('masw_id', site['ert_id'].replace('ERT', 'MW'))
        bh = site['bh']
        candidates = [
            os.path.join(project.masw_input_dir, f'{mw_id}.csv'),
            os.path.join(project.masw_input_dir, f'{mw_id}_shot.csv'),
            os.path.join(project.masw_input_dir, f'{bh}.csv'),
        ]
        input_file = next((c for c in candidates if os.path.exists(c)), None)
        if input_file is None:
            continue
        try:
            r = process_masw_station(input_file, project.masw_output_dir,
                                     station_id=mw_id, sr_hz=sr, dx_m=dx,
                                     verbose=verbose)
            r['bh'] = bh
            r['group'] = site['group']
            results.append(r)
            if progress_callback:
                progress_callback(i + 1, len(sites), r)
        except Exception as e:
            print(f"  Error processing {mw_id}: {e}")
    pd.DataFrame(results).to_csv(
        os.path.join(project.masw_output_dir, 'MASW_summary.csv'), index=False)
    return results
