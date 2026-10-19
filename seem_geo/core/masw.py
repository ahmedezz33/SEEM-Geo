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
                   n_f=100, n_v=120):
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


def auto_pick_dispersion(f_axis, v_axis, FV, threshold=0.85):
    """Pick fundamental-mode dispersion by max-energy ridge.

    Uses quadratic (parabolic) peak-fitting around the argmax to get
    sub-grid velocity precision (~0.1 m/s instead of the v_axis step).
    This matters when two surveys sit in similar material: the raw argmax
    would snap both to the same v-bin and hide genuine field variability.
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
    return np.array(picks)


def plot_dispersion_image(f_axis, v_axis, FV, picks, out_png, station_id="MW-??"):
    fig, ax = plt.subplots(figsize=(10, 6))
    F, V = np.meshgrid(f_axis, v_axis, indexing='ij')
    im = ax.pcolormesh(F, V, FV, cmap='jet', shading='auto', vmin=0, vmax=1)
    if len(picks) > 0:
        ax.plot(picks[:, 0], picks[:, 1], 'wo-', markersize=5,
                markeredgecolor='black', linewidth=1.2, label='Fundamental mode')
        ax.legend(loc='upper right', fontsize=9)
    ax.set_xlabel('Frequency (Hz)', fontsize=11)
    ax.set_ylabel('Phase velocity (m/s)', fontsize=11)
    ax.set_title(f'{station_id} - f-v Dispersion Image',
                 fontsize=13, fontweight='bold')
    plt.colorbar(im, ax=ax, label='Normalized energy')
    plt.tight_layout()
    plt.savefig(out_png, dpi=180, bbox_inches='tight', facecolor='white')
    plt.close()
    return out_png


def dispersion_to_vs_profile(picks, n_layers=8, max_depth=30.0):
    """Simple half-wavelength depth transform."""
    if len(picks) < 3:
        return np.array([0, max_depth]), np.array([250.0])
    depths = 1.045 * picks[:, 1] / picks[:, 0] / 2.5
    vs = picks[:, 1] / 1.09
    z_bounds = np.linspace(0, max_depth, n_layers + 1)
    vs_layers = np.zeros(n_layers)
    for i in range(n_layers):
        mask = (depths >= z_bounds[i]) & (depths < z_bounds[i + 1])
        if mask.sum() > 0:
            vs_layers[i] = np.mean(vs[mask])
        elif i > 0:
            vs_layers[i] = vs_layers[i - 1]
        else:
            vs_layers[i] = vs.mean() if len(vs) > 0 else 250.0
    for i in range(n_layers):
        if vs_layers[i] == 0:
            vs_layers[i] = vs_layers[i - 1] if i > 0 else 250.0
    return z_bounds, vs_layers


def compute_vs30(z_bounds, vs_layers):
    """Travel-time weighted average over top 30 m."""
    if len(vs_layers) == 0:
        return 0.0
    t_total = 0.0
    z_total = 0.0
    for i, vs in enumerate(vs_layers):
        z_top = z_bounds[i]
        z_bot = z_bounds[i + 1]
        if z_top >= 30:
            break
        dz = min(z_bot, 30) - z_top
        if dz > 0 and vs > 0:
            t_total += dz / vs
            z_total += dz
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


def plot_vs_profile(z_bounds, vs_layers, out_png, station_id="MW-??", vs30=None):
    fig, ax = plt.subplots(figsize=(6, 8))
    for i, vs in enumerate(vs_layers):
        ax.fill_betweenx([z_bounds[i], z_bounds[i + 1]], 0, vs,
                         facecolor='steelblue', edgecolor='black', linewidth=0.6)
        ax.text(vs + 10, (z_bounds[i] + z_bounds[i + 1]) / 2,
                f'{vs:.0f}', va='center', fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel('Shear-wave velocity Vs (m/s)', fontsize=11)
    ax.set_ylabel('Depth (m)', fontsize=11)
    title = f'{station_id} - Vs Profile'
    if vs30 is not None:
        title += f'  |  Vs30 = {vs30:.0f} m/s'
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.axhline(30, color='red', linestyle='--', linewidth=1.0, alpha=0.6)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_png, dpi=180, bbox_inches='tight', facecolor='white')
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
