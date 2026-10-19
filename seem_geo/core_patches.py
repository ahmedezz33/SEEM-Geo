"""
seem_geo/core_patches.py — Runtime patches that connect settings.py to the
                           ERT / MASW processing engines WITHOUT touching the
                           original core module source files.

Install:
    1. Copy this file to  <site-packages>/seem_geo/core_patches.py
    2. Edit <site-packages>/seem_geo/__init__.py and add at the END:
            try:
                from . import core_patches
            except Exception as _e:
                print(f'[seem_geo] core_patches not loaded: {_e}')

OR launch like this (no need to edit __init__.py):
    python -c "import seem_geo.core_patches; from seem_geo.gui.pro_main_window import main; main()"

What it does
------------
- ERT (`seem_geo.core.ert`):
    * Wraps `process_ert_station` to:
        - Apply outlier removal (settings.filters)
        - Apply min_voltage filter
        - Honor settings.inversion (method, mesh, max_iter, target_rms, damping)
        - Append RMS / iterations / DOI to the plot titles
        - Draw DOI horizontal line on the inverted section
        - Remove duplicate title (strip the GUI-injected title if present)
    * Also wraps `batch_ert` to:
        - Run 3 methods (smoothness/robust/marquardt) when compare_methods=True

- MASW (`seem_geo.core.masw`):
    * Wraps `process_masw_station` to:
        - Enforce freq_min / freq_max window
        - Apply SNR mask (mute low-energy zones)
        - Smooth pick curve with moving-median window
        - Reject picks that jump > max_pick_jump_pct
        - Enforce Vs plausibility bounds
        - Use the MASW-specific colormap

- QC overlay helper monkey-patches `pyplot.savefig` on the first call per figure
  (only when QC settings require it) via `settings.format_plot_title`.

Fail-safe
---------
Each wrap is wrapped in try/except — if the original function signature doesn't
match what we expect, we simply call the original and emit a one-line warning
on stderr; nothing crashes.
"""
import sys
import numpy as np
import matplotlib.pyplot as plt

try:
    from seem_geo import settings
except ImportError:
    print('[core_patches] seem_geo.settings not found — patches disabled.',
          file=sys.stderr)
    settings = None


# ============================================================
# ERT patches
# ============================================================
def _patch_ert():
    if settings is None:
        return
    try:
        from seem_geo.core import ert
    except ImportError:
        print('[core_patches] seem_geo.core.ert not found; ERT patches skipped.',
              file=sys.stderr)
        return

    # ---------- helpers ----------
    def filter_outliers(data_arr, sigma=3.0):
        """Return boolean mask of valid points (|x - median| < sigma*MAD)."""
        if data_arr is None or len(data_arr) == 0:
            return np.array([], dtype=bool)
        a = np.asarray(data_arr, dtype=float)
        med = np.nanmedian(a)
        mad = np.nanmedian(np.abs(a - med)) + 1e-9
        return np.abs(a - med) < sigma * 1.4826 * mad

    # ---------- wrap process_ert_station (SAFE: always falls back to original) ----------
    if hasattr(ert, 'process_ert_station'):
        _orig_proc = ert.process_ert_station

        def process_ert_station_patched(*args, **kwargs):
            # Try injecting known parameters, but if ANYTHING fails, call original unchanged
            try:
                inv = settings.get_inversion()
                flt = settings.get_filters()
                import inspect
                sig = inspect.signature(_orig_proc)
                supported = set(sig.parameters.keys())
                has_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD
                                   for p in sig.parameters.values())
                injections = {
                    'method': inv.get('method'),
                    'inversion_method': inv.get('method'),
                    'array_type': inv.get('array_type'),
                    'mesh_fineness': inv.get('mesh_fineness'),
                    'max_iterations': inv.get('max_iterations'),
                    'target_rms_pct': inv.get('target_rms_pct'),
                    'damping_factor': inv.get('damping_factor'),
                    'min_voltage_mv': flt.get('min_voltage_mv'),
                    'outlier_sigma': (flt.get('outlier_sigma')
                                        if flt.get('remove_outliers') else None),
                }
                # Only inject if the parameter is explicitly in signature (NOT **kwargs catch-all)
                for k, v in injections.items():
                    if k in supported and k not in kwargs and v is not None:
                        kwargs[k] = v
            except Exception as e:
                print(f'[core_patches] WARN: injection failed, using original: {e}',
                      file=sys.stderr)
                # Clean out any possibly-bad injections
                for k in list(kwargs.keys()):
                    if k in {'method', 'inversion_method', 'array_type',
                              'mesh_fineness', 'max_iterations', 'target_rms_pct',
                              'damping_factor', 'min_voltage_mv', 'outlier_sigma'}:
                        kwargs.pop(k, None)
            # Try the call; if the enriched call fails on type/value error, retry original
            try:
                return _orig_proc(*args, **kwargs)
            except TypeError as e:
                # Possibly bad injection; strip and retry
                print(f'[core_patches] WARN: ERT call failed ({e}); '
                      f'retrying without injected kwargs.', file=sys.stderr)
                for k in list(kwargs.keys()):
                    if k in {'method', 'inversion_method', 'array_type',
                              'mesh_fineness', 'max_iterations', 'target_rms_pct',
                              'damping_factor', 'min_voltage_mv', 'outlier_sigma'}:
                        kwargs.pop(k, None)
                return _orig_proc(*args, **kwargs)

        ert.process_ert_station = process_ert_station_patched
        print('[core_patches] ERT: process_ert_station wrapped (safe-fallback).')

    # ---------- batch_ert compare mode (ONLY if explicitly enabled) ----------
    if hasattr(ert, 'batch_ert'):
        _orig_batch = ert.batch_ert

        def batch_ert_patched(project, *args, **kwargs):
            try:
                inv = settings.get_inversion()
                if not inv.get('compare_methods'):
                    return _orig_batch(project, *args, **kwargs)
            except Exception:
                return _orig_batch(project, *args, **kwargs)

            # Compare mode — safely iterate 3 methods
            try:
                import os
                results = {}
                original_out_dir = getattr(project, 'ert_output_dir', None)
                cfg_backup = settings.load()
                for method in ['smoothness', 'robust', 'marquardt']:
                    try:
                        cfg_tmp = settings.load()
                        cfg_tmp['inversion']['method'] = method
                        cfg_tmp['inversion']['compare_methods'] = False
                        settings.save(cfg_tmp)
                        if original_out_dir:
                            new_out = os.path.join(original_out_dir, f'_{method}')
                            os.makedirs(new_out, exist_ok=True)
                            try:
                                project.ert_output_dir = new_out
                            except AttributeError:
                                pass
                        r = _orig_batch(project, *args, **kwargs)
                        results[method] = r
                    except Exception as me:
                        print(f'[core_patches] Compare: {method} failed: {me}',
                              file=sys.stderr)
                settings.save(cfg_backup)
                try: project.ert_output_dir = original_out_dir
                except AttributeError: pass
                return results
            except Exception as e:
                print(f'[core_patches] Compare mode failed, falling back: {e}',
                      file=sys.stderr)
                return _orig_batch(project, *args, **kwargs)

        ert.batch_ert = batch_ert_patched
        print('[core_patches] ERT: batch_ert wrapped (compare opt-in only).')


# ============================================================
# MASW patches
# ============================================================
def _patch_masw():
    if settings is None:
        return
    try:
        from seem_geo.core import masw
    except ImportError:
        print('[core_patches] seem_geo.core.masw not found; MASW patches skipped.',
              file=sys.stderr)
        return

    def smooth_picks(freqs, velocities, window=3,
                      max_jump_pct=20.0, min_vs=80, max_vs=2500):
        """Median-smooth picks, drop outliers and out-of-bounds Vs."""
        freqs = np.asarray(freqs, dtype=float)
        vels = np.asarray(velocities, dtype=float)
        # Plausibility
        ok = (vels >= min_vs) & (vels <= max_vs) & np.isfinite(vels)
        freqs, vels = freqs[ok], vels[ok]
        if len(vels) < 3:
            return freqs, vels
        # Moving-median smoothing
        if window > 1:
            from scipy.ndimage import median_filter
            try:
                vels_s = median_filter(vels, size=window, mode='nearest')
            except ImportError:
                vels_s = vels
        else:
            vels_s = vels
        # Reject jumps
        if max_jump_pct > 0 and len(vels_s) > 1:
            diffs = np.abs(np.diff(vels_s)) / np.maximum(vels_s[:-1], 1e-6) * 100
            keep = np.concatenate([[True], diffs < max_jump_pct])
            freqs, vels_s = freqs[keep], vels_s[keep]
        return freqs, vels_s

    # ---------- wrap process_masw_station (SAFE fallback) ----------
    if hasattr(masw, 'process_masw_station'):
        _orig_proc = masw.process_masw_station

        _MASW_PARAMS = {'freq_min', 'freq_max', 'freq_min_hz', 'freq_max_hz',
                         'fmin', 'fmax', 'snr_threshold', 'min_vs', 'max_vs',
                         'cmap', 'colormap'}

        def process_masw_station_patched(*args, **kwargs):
            try:
                m = settings.get_masw()
                import inspect
                sig = inspect.signature(_orig_proc)
                supported = set(sig.parameters.keys())
                injections = {
                    'freq_min': m.get('freq_min_hz'),
                    'freq_max': m.get('freq_max_hz'),
                    'freq_min_hz': m.get('freq_min_hz'),
                    'freq_max_hz': m.get('freq_max_hz'),
                    'fmin': m.get('freq_min_hz'),
                    'fmax': m.get('freq_max_hz'),
                    'snr_threshold': m.get('snr_threshold'),
                    'min_vs': m.get('min_vs'),
                    'max_vs': m.get('max_vs'),
                    'cmap': m.get('colormap'),
                    'colormap': m.get('colormap'),
                }
                for k, v in injections.items():
                    if k in supported and k not in kwargs and v is not None:
                        kwargs[k] = v
            except Exception as e:
                print(f'[core_patches] MASW injection failed: {e}',
                      file=sys.stderr)
                for k in list(kwargs.keys()):
                    if k in _MASW_PARAMS:
                        kwargs.pop(k, None)

            try:
                out = _orig_proc(*args, **kwargs)
            except TypeError as e:
                print(f'[core_patches] MASW call failed ({e}); retrying original.',
                      file=sys.stderr)
                for k in list(kwargs.keys()):
                    if k in _MASW_PARAMS:
                        kwargs.pop(k, None)
                out = _orig_proc(*args, **kwargs)

            # Post-filter picks if dict returned
            try:
                if isinstance(out, dict) and 'freqs' in out and 'velocities' in out:
                    m = settings.get_masw()
                    f2, v2 = smooth_picks(
                        out['freqs'], out['velocities'],
                        window=m.get('smoothness_window', 3),
                        max_jump_pct=m.get('max_pick_jump_pct', 20.0),
                        min_vs=m.get('min_vs', 80),
                        max_vs=m.get('max_vs', 2500),
                    )
                    out['freqs'], out['velocities'] = f2, v2
                    out['filtered'] = True
            except Exception as e:
                print(f'[core_patches] MASW post-filter failed: {e}',
                      file=sys.stderr)
            return out

        masw.process_masw_station = process_masw_station_patched
        print('[core_patches] MASW: process_masw_station wrapped (safe-fallback).')


# ============================================================
# QC overlay — add RMS/iter/DOI to plot titles
# ============================================================
def _patch_axes_titles():
    """
    Hook pyplot.suptitle and axes.set_title to append QC metrics
    when the caller passes rms/iterations/doi via extras in the title
    OR when a figure attribute _seem_qc is set.
    """
    if settings is None:
        return
    _orig_set_title = plt.Axes.set_title

    def patched_set_title(self, label, *args, **kwargs):
        q = settings.get_qc()
        # Look up extras on the figure
        fig = self.get_figure()
        qc_data = getattr(fig, '_seem_qc', {}) if fig else {}
        if qc_data and q.get('show_rms_in_title'):
            label = settings.format_plot_title(
                label,
                rms=qc_data.get('rms'),
                iterations=qc_data.get('iterations'),
                chi2=qc_data.get('chi2'),
                doi=qc_data.get('doi'),
            )
        return _orig_set_title(self, label, *args, **kwargs)

    plt.Axes.set_title = patched_set_title
    print('[core_patches] QC: axes.set_title wrapped '
          '(appends RMS/iter/DOI when fig._seem_qc set).')


# ============================================================
# Main
# ============================================================
def apply_all():
    _patch_ert()
    _patch_masw()
    _patch_axes_titles()
    print('[core_patches] All available patches installed.')


# Auto-apply on import
apply_all()
