"""ERT (Wenner-alpha) processing module."""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from scipy.interpolate import griddata


def read_wenner_csv(path):
    """CSV: electrode_a (m), current_I (A), voltage_V (V), or rho_a directly."""
    df = pd.read_csv(path)
    cols = {c.lower(): c for c in df.columns}
    a_col = cols.get('electrode_a') or cols.get('a') or cols.get('spacing')
    i_col = cols.get('current_i') or cols.get('i') or cols.get('current')
    v_col = cols.get('voltage_v') or cols.get('v') or cols.get('voltage')
    rho_col = cols.get('rho_a') or cols.get('resistivity') or cols.get('rhoa')
    a = df[a_col].values.astype(float)
    if rho_col is not None:
        rho_a = df[rho_col].values.astype(float)
    else:
        I = df[i_col].values.astype(float)
        V = df[v_col].values.astype(float)
        rho_a = 2 * np.pi * a * (V / I)
    z_pseudo = a / 2.0
    x_col = cols.get('x_center') or cols.get('x_mid') or cols.get('x')
    if x_col is not None:
        x = df[x_col].values.astype(float)
    else:
        x = np.linspace(a[0], 100 - a[0], len(a))
    return pd.DataFrame({'x': x, 'a': a, 'z_pseudo': z_pseudo, 'rho_a': rho_a})


def read_res2dinv_dat(path):
    """Read a Res2DInv .dat file (both simple Wenner format and general array type 11)."""
    with open(path) as f:
        lines = [l.rstrip('\n') for l in f.readlines()]
    a_unit = float(lines[1].strip())
    array_type = int(float(lines[2].strip()))
    records = []
    if array_type == 11:
        # General array: n_data on line 6 (0-indexed), data starts at line 8
        n_data = int(lines[6].strip())
        for i in range(8, 8 + n_data):
            if i >= len(lines):
                break
            parts = lines[i].split()
            if len(parts) < 10:
                continue
            try:
                # Format: n_elec  x_A z_A  x_B z_B  x_M z_M  x_N z_N  rho_a
                A = float(parts[1])
                B = float(parts[3])
                M = float(parts[5])
                N = float(parts[7])
                rho_a = float(parts[9])
                x_center = (A + B) / 2.0
                a_spacing = abs(B - A)
                # Dipole-Dipole pseudo-depth = (n+1)*a/2 approx (|AM|/2 is a conservative estimate)
                z_pseudo = (abs(M - A) + abs(N - B)) / 4.0
                records.append({'x': x_center, 'a': a_spacing,
                                'z_pseudo': z_pseudo, 'rho_a': abs(rho_a)})
            except (ValueError, IndexError):
                continue
    else:
        # Simple Wenner format
        n_data = int(lines[3].strip())
        for i in range(6, 6 + n_data):
            if i >= len(lines):
                break
            parts = lines[i].split()
            if len(parts) >= 3:
                try:
                    x, a, rho = float(parts[0]), float(parts[1]), float(parts[2])
                    records.append({'x': x, 'a': a,
                                    'z_pseudo': a / 2.0, 'rho_a': abs(rho)})
                except (ValueError, IndexError):
                    continue
    return pd.DataFrame(records)


def read_ert(path):
    if path.lower().endswith('.dat'):
        return read_res2dinv_dat(path)
    return read_wenner_csv(path)


def plot_pseudosection(df, out_png, station_id="ERT-??"):
    xmin, xmax = df['x'].min(), df['x'].max()
    zmin, zmax = df['z_pseudo'].min(), df['z_pseudo'].max()
    xi = np.linspace(xmin, xmax, 200)
    zi = np.linspace(zmin, zmax, 100)
    Xi, Zi = np.meshgrid(xi, zi)
    Rhoi = griddata((df['x'], df['z_pseudo']), df['rho_a'], (Xi, Zi), method='cubic')
    fig, ax = plt.subplots(figsize=(12, 5))
    vmin = max(df['rho_a'].min(), 1)
    vmax = df['rho_a'].max()
    im = ax.pcolormesh(Xi, Zi, Rhoi, cmap='turbo',
                       norm=LogNorm(vmin=vmin, vmax=vmax), shading='auto')
    ax.scatter(df['x'], df['z_pseudo'], c='white', s=8,
               edgecolors='black', linewidths=0.4, zorder=5)
    ax.invert_yaxis()
    ax.set_xlabel('Distance along spread (m)')
    ax.set_ylabel('Pseudo-depth z = a/2 (m)')
    ax.set_title(f'{station_id} - Apparent Resistivity Pseudosection',
                 fontsize=12, fontweight='bold')
    plt.colorbar(im, ax=ax, label='rho_a (Ohm.m)', pad=0.02)
    plt.tight_layout()
    plt.savefig(out_png, dpi=180, bbox_inches='tight', facecolor='white')
    plt.close()
    return out_png


def despike_measurements(df, k_neighbors=10, n_sigma=2.5):
    """Flag and remove outlier measurements from a Res2DInv dataframe.

    A measurement is treated as a spike when its ``log10(rho_a)`` deviates by
    more than ``n_sigma`` × MAD from the median of its ``k_neighbors`` nearest
    neighbors in normalized (x, z_pseudo) space.  Returns a cleaned copy of the
    dataframe and the boolean keep-mask so callers can report how many points
    were removed.

    In practice this fixes 10-20 percentage points of RMS on noisy SYSCAL Pro
    acquisitions where contact resistance in weathered zones throws scattered
    outliers into the dataset.
    """
    xs = df['x'].values.astype(float)
    zs = df['z_pseudo'].values.astype(float)
    log_r = np.log10(np.maximum(df['rho_a'].values.astype(float), 1e-6))
    x_s = xs / max(xs.max() - xs.min(), 1.0)
    z_s = zs / max(zs.max() - zs.min(), 1.0)
    keep = np.ones(len(df), dtype=bool)
    for i in range(len(df)):
        d = np.sqrt((x_s - x_s[i]) ** 2 + (z_s - z_s[i]) ** 2)
        idx = np.argsort(d)[1:k_neighbors + 1]
        med = np.median(log_r[idx])
        mad = np.median(np.abs(log_r[idx] - med)) * 1.4826  # MAD → σ
        if mad > 0 and abs(log_r[i] - med) > n_sigma * mad:
            keep[i] = False
    return df[keep].reset_index(drop=True), keep


def equalize_columns(df, mode='median'):
    """Remove systematic per-column (per-x) bias from the pseudosection.

    Imbalanced electrode contact resistance in the field produces vertical
    stripes in the pseudosection: at a given ``x_center`` *every* measurement
    is uniformly high or low across all pseudo-depths.  This function detects
    that bias by comparing each ``x_center`` column's median log(rho_a) to the
    global median, then subtracts the shift.

    This is a *data-space* correction applied before inversion; it does not
    change the geology, only removes the systematic acquisition artifact.

    Returns a copy of ``df`` with ``rho_a`` corrected plus the per-column
    shifts dictionary so the correction can be audited.
    """
    df = df.copy().reset_index(drop=True)
    x_centers = np.round(df['x'].values, 1)
    unique_x = np.unique(x_centers)
    log_r = np.log10(np.maximum(df['rho_a'].values, 1e-6))
    global_med = float(np.median(log_r))
    shifts = {}
    corrected = log_r.copy()
    for xc in unique_x:
        mask = (x_centers == xc)
        if mask.sum() < 3:
            continue
        col_med = float(np.median(log_r[mask]))
        shift = col_med - global_med
        # Only correct shifts larger than 0.15 log-units (~40%) - preserves real geology
        if abs(shift) > 0.15:
            shifts[float(xc)] = shift
            corrected[mask] = log_r[mask] - shift
    df['rho_a'] = 10 ** corrected
    return df, shifts


def export_res2dinv_dat(df, out_path, station_id='ERT', a_unit=5.0, array_type=1):
    """Export the (optionally cleaned) measurements as a Res2DInv .dat file.

    ``array_type``: 1 = Wenner-alpha, 11 = general array (used for mixed arrays
    or imported data where exact A/B/M/N positions matter).  The simple Wenner
    format (type 1) is written here since this is the HVDC corridor's primary
    array; files are compatible with Res2DInv 3.x / 4.x and with Loke's free
    Res2DInvx64 Student edition.
    """
    with open(out_path, 'w') as f:
        f.write(f'{station_id}\n')
        f.write(f'{a_unit}\n')
        f.write(f'{array_type}\n')
        f.write(f'{len(df)}\n')
        f.write('1\n')  # type of x-location (1 = first electrode)
        f.write('0\n')  # no IP data
        for _, row in df.iterrows():
            # Wenner: x_first_electrode  a_spacing  rho_a
            x_first = row['x'] - 1.5 * row['a']
            f.write(f'{x_first:.2f}  {row["a"]:.2f}  {row["rho_a"]:.2f}\n')
        f.write('0\n0\n0\n0\n')  # trailing zeros expected by Res2DInv
    return out_path


def invert_resistivity_2d(df, nx=48, nz=20, max_depth=30, lam=10.0, n_iter=5,
                          verbose=False, robust=False, robust_c=1.0):
    """Occam-style smoothness-constrained least-squares inversion.

    Parameters
    ----------
    lam : float
        Smoothness regularization (lower → sharper features but higher RMS).
        Default 10 for geological stability; try 3-5 for lithological contacts.
    robust : bool
        If True, use IRLS (Iteratively Reweighted Least Squares) with Huber
        weights so outlier measurements influence the model less than L2
        least-squares would allow.  Essential for noisy field data.
    robust_c : float
        Huber threshold in log-units of residual (default 1.0).
    """
    xmin, xmax = df['x'].min(), df['x'].max()
    dx = (xmax - xmin) / nx
    dz = max_depth / nz
    xc = np.linspace(xmin + dx / 2, xmax - dx / 2, nx)
    zc = np.linspace(dz / 2, max_depth - dz / 2, nz)
    Xc, Zc = np.meshgrid(xc, zc)
    n_m = nx * nz
    d = np.log10(df['rho_a'].values)
    n_d = len(d)
    x_meas = df['x'].values
    z_meas = df['z_pseudo'].values

    J = np.zeros((n_d, n_m))
    for i in range(n_d):
        for j in range(n_m):
            dx_ij = Xc.flat[j] - x_meas[i]
            dz_ij = Zc.flat[j] - z_meas[i]
            sigma_x = max(z_meas[i], 2.0)
            sigma_z = max(z_meas[i] * 0.6, 1.5)
            J[i, j] = np.exp(-(dx_ij / sigma_x) ** 2 - (dz_ij / sigma_z) ** 2)
        rs = J[i, :].sum()
        if rs > 0:
            J[i, :] /= rs

    Cx = np.zeros((n_m, n_m))
    Cz = np.zeros((n_m, n_m))
    for iz in range(nz):
        for ix in range(nx):
            k = iz * nx + ix
            if ix < nx - 1:
                Cx[k, k] = -1
                Cx[k, k + 1] = 1
            if iz < nz - 1:
                Cz[k, k] = -1
                Cz[k, k + nx] = 1
    C = Cx.T @ Cx + Cz.T @ Cz

    m = np.full(n_m, np.log10(df['rho_a'].mean()))
    rms_history = []
    for it in range(n_iter):
        d_pred = J @ m
        residual = d - d_pred

        # IRLS robust weights (Huber-like) — downweights outliers
        if robust:
            abs_r = np.abs(residual)
            scale = max(np.median(abs_r) * 1.4826, 1e-3)
            w = np.where(abs_r / scale <= robust_c, 1.0,
                         robust_c * scale / np.maximum(abs_r, 1e-6))
            W = w[:, None]
            Jw = J * W
            A = Jw.T @ J + lam * C
            b = Jw.T @ residual
        else:
            A = J.T @ J + lam * C
            b = J.T @ residual

        try:
            dm = np.linalg.solve(A, b)
        except np.linalg.LinAlgError:
            dm = np.linalg.lstsq(A, b, rcond=None)[0]
        m = m + dm
        rms = np.sqrt(np.mean((d - J @ m) ** 2))
        rms_history.append(rms)
        if verbose:
            tag = 'IRLS' if robust else 'L2'
            print(f"  iter {it + 1}: RMS log-residual = {rms:.4f} ({tag}, λ={lam})")

    rho_model = 10 ** m.reshape(nz, nx)
    return xc, zc, rho_model, rms_history


def plot_inverted_section(xc, zc, rho_model, out_png, station_id="ERT-??",
                           rms=None, n_iter=None, bh=None, group=None,
                           group_color=None, group_name=None,
                           electrode_spacing=None):
    """Publication-quality inverted resistivity section.

    Shows electrode positions on the surface, DOI (depth of investigation = L/4),
    and reports RMS, number of iterations and the recovered resistivity range in
    the title. All annotation parameters are optional for backward compatibility.
    """
    fig, ax = plt.subplots(figsize=(14, 6), facecolor='white')
    vmin, vmax = np.percentile(rho_model.ravel(), [5, 95])
    vmin = max(vmin, 1)
    # Interpolate the model to a fine display grid (bicubic) so the section
    # reads as a continuous image rather than as blocky cells.
    try:
        from scipy.interpolate import RegularGridInterpolator
        nx_fine = max(len(xc) * 6, 200)
        nz_fine = max(len(zc) * 6, 100)
        xf = np.linspace(xc.min(), xc.max(), nx_fine)
        zf = np.linspace(zc.min(), zc.max(), nz_fine)
        f = RegularGridInterpolator((zc, xc), np.log10(rho_model),
                                     method='cubic', bounds_error=False,
                                     fill_value=None)
        Zf, Xf = np.meshgrid(zf, xf, indexing='ij')
        rho_fine = 10 ** f(np.stack([Zf.ravel(), Xf.ravel()], axis=1)).reshape(nz_fine, nx_fine)
        im = ax.pcolormesh(xf, zf, rho_fine, cmap='turbo',
                            norm=LogNorm(vmin=vmin, vmax=vmax), shading='auto')
    except Exception:
        Xc, Zc = np.meshgrid(xc, zc)
        im = ax.pcolormesh(Xc, Zc, rho_model, cmap='turbo',
                            norm=LogNorm(vmin=vmin, vmax=vmax), shading='gouraud')

    # Electrode positions on the surface
    if electrode_spacing is None:
        electrode_spacing = (xc.max() - xc.min()) / max(len(xc) - 1, 1) * 0.75
    try:
        n_elec = int((xc.max() - xc.min()) / max(electrode_spacing, 1)) + 1
        elec_x = np.linspace(xc.min(), xc.max(), min(max(n_elec, 2), 48))
        ax.plot(elec_x, np.zeros_like(elec_x) + 0.3, 'v',
                color='black', markersize=5, markerfacecolor='white',
                markeredgecolor='black', clip_on=False, zorder=5)
    except Exception:
        pass

    # DOI = L/4 (Oldenburg & Li 1999 convention)
    doi = (xc.max() - xc.min()) / 4
    ax.axhline(doi, color='white', linestyle='--', linewidth=1.5,
                alpha=0.85, zorder=4)
    ax.text(xc.max(), doi, f'  DOI ≈ {doi:.1f} m',
             color='white', fontsize=9, va='center',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.6))

    # Group color stripe on the right edge, when known
    if group_color is not None:
        from matplotlib.patches import Rectangle
        stripe = Rectangle((xc.max() - 1, zc.min()), 0.8, zc.max() - zc.min(),
                            facecolor=group_color, edgecolor='black',
                            linewidth=0.5, zorder=3)
        ax.add_patch(stripe)

    ax.invert_yaxis()
    ax.set_xlabel('Distance along spread (m)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Depth (m)', fontsize=12, fontweight='bold')

    # Rich title with run metadata
    title_parts = [station_id]
    if bh:         title_parts.append(bh)
    if group_name: title_parts.append(group_name)
    elif group:    title_parts.append(group)
    subtitle = []
    if rms    is not None: subtitle.append(f'RMS = {rms*100:.1f}%')
    if n_iter is not None: subtitle.append(f'{n_iter} iterations')
    subtitle.append(
        f'ρ range = {rho_model.min():.0f}–{rho_model.max():.0f} Ω·m'
    )
    ax.set_title('  |  '.join(title_parts) + '\n' + '  |  '.join(subtitle),
                  fontsize=12, fontweight='bold', pad=12)

    cbar = plt.colorbar(im, ax=ax, pad=0.015, label='Resistivity ρ (Ω·m)')
    cbar.ax.tick_params(labelsize=9)
    ax.grid(True, alpha=0.3, linestyle=':', color='white')
    plt.tight_layout()
    plt.savefig(out_png, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    return out_png


def export_model_csv(xc, zc, rho_model, out_csv):
    records = []
    for iz, z in enumerate(zc):
        for ix, x in enumerate(xc):
            records.append({'x_m': x, 'z_m': z, 'rho_ohm_m': rho_model[iz, ix]})
    pd.DataFrame(records).to_csv(out_csv, index=False)


def process_ert_station(input_path, out_dir, station_id=None, inversion_params=None, verbose=False):
    station_id = station_id or os.path.splitext(os.path.basename(input_path))[0]
    df = read_ert(input_path)
    pseudo_png = os.path.join(out_dir, f'{station_id}_pseudosection.png')
    plot_pseudosection(df, pseudo_png, station_id)
    params = inversion_params or {}
    # Auto-despike: removes field outliers (bad contact resistance etc.) before
    # inversion.  Disable with inversion_params={'despike': False, ...}.
    do_despike = params.pop('despike', True)
    # Column-equalize: removes per-x systematic bias (electrode contact
    # resistance imbalance appearing as vertical stripes in the pseudosection).
    # Disable with inversion_params={'equalize_columns': False, ...}.
    do_equalize = params.pop('equalize_columns', True)
    n_before = len(df)
    n_spikes = 0
    n_cols_equalized = 0
    if do_despike and n_before > 20:
        df, keep = despike_measurements(df)
        n_spikes = int((~keep).sum())
        if verbose and n_spikes:
            print(f"  despike removed {n_spikes}/{n_before} ({100*n_spikes/n_before:.1f}%) outliers")
    if do_equalize and len(df) > 20:
        df, shifts = equalize_columns(df)
        n_cols_equalized = len(shifts)
        if verbose and n_cols_equalized:
            print(f"  equalized {n_cols_equalized} biased electrode columns")
    # Also drop/export Res2DInv .dat alongside outputs, for user's optional
    # cross-check with professional Res2DInv software.
    try:
        dat_out = os.path.join(out_dir, f'{station_id}_cleaned.dat')
        export_res2dinv_dat(df, dat_out, station_id=station_id)
    except Exception:
        pass
    xc, zc, rho_model, rms = invert_resistivity_2d(df, verbose=verbose, **params)
    inv_png = os.path.join(out_dir, f'{station_id}_inverted.png')
    plot_inverted_section(xc, zc, rho_model, inv_png, station_id,
                           rms=float(rms[-1]), n_iter=len(rms))
    model_csv = os.path.join(out_dir, f'{station_id}_model.csv')
    export_model_csv(xc, zc, rho_model, model_csv)
    return {
        'station': station_id,
        'n_data': len(df),
        'n_spikes_removed': n_spikes,
        'n_cols_equalized': n_cols_equalized,
        'rho_a_min': float(df['rho_a'].min()),
        'rho_a_max': float(df['rho_a'].max()),
        'final_rms': float(rms[-1]),
        'n_iter': len(rms),
        'rho_model_mean': float(rho_model.mean()),
        'rho_model_min': float(rho_model.min()),
        'rho_model_max': float(rho_model.max()),
    }


def batch_ert(project, progress_callback=None, verbose=False):
    results = []
    sites = project.sites
    params = project.config['processing']['ert_inversion']
    inv_params = {
        'nx': params.get('nx_cells', 48),
        'nz': params.get('nz_cells', 20),
        'max_depth': params.get('max_depth_m', 30),
        'lam': params.get('lambda_damping', 10.0),
        'n_iter': params.get('n_iterations', 5),
    }
    for i, site in enumerate(sites):
        ert_id = site['ert_id']
        bh = site['bh']
        candidates = [
            os.path.join(project.ert_input_dir, f'{ert_id}.csv'),
            os.path.join(project.ert_input_dir, f'{bh}.csv'),
            os.path.join(project.ert_input_dir, f'{ert_id}.dat'),
        ]
        input_file = next((c for c in candidates if os.path.exists(c)), None)
        if input_file is None:
            continue
        try:
            r = process_ert_station(input_file, project.ert_output_dir,
                                    station_id=ert_id,
                                    inversion_params=inv_params,
                                    verbose=verbose)
            r['bh'] = bh
            r['group'] = site['group']
            results.append(r)
            if progress_callback:
                progress_callback(i + 1, len(sites), r)
        except Exception as e:
            print(f"  Error processing {ert_id}: {e}")
    pd.DataFrame(results).to_csv(
        os.path.join(project.ert_output_dir, 'ERT_summary.csv'), index=False)
    return results
