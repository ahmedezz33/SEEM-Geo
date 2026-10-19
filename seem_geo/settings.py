"""
seem_geo/settings.py — Comprehensive settings for SEEM Geo (v2)

Five-tab dialog:
    1. Image Output   - DPI, size, colors, format
    2. Inversion      - Method, mesh fineness, data type, convergence
    3. Data Filters   - Outlier removal, voltage/reciprocal filters
    4. QC Display     - RMS/iter/DOI/Chi2 overlays, duplicate-title filter
    5. Confirmation   - Field data preview + confirmation workflow

Persistent at ~/.seem_geo_settings.json
Auto-applied to matplotlib on import.
"""
import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib

# ===================================================================
# Config
# ===================================================================
CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.seem_geo_settings.json')

DEFAULTS = {
    # ---------- Image Output ----------
    'image': {
        'dpi': 300,
        'fig_width': 14.0,
        'fig_height': 9.0,
        'font_size': 11,
        'colormap': 'viridis',
        'img_format': 'png',
        'tight_layout': True,
        'transparent': False,
        'force_dpi': True,
    },
    # ---------- Inversion ----------
    'inversion': {
        'array_type': 'wenner',          # wenner | schlumberger | dipole_dipole | pole_dipole
        'mesh_fineness': 4,              # 2=coarse 4=standard 6=fine 8=very fine
        'method': 'smoothness',          # smoothness | robust | marquardt
        'max_iterations': 10,
        'target_rms_pct': 5.0,
        'damping_factor': 0.1,
        'h_v_smoothness_ratio': 1.0,
        'compare_methods': False,        # run all 3 and compare
        'use_topography': False,
        'wavelet_filter': False,
    },
    # ---------- Data Filters (ERT) ----------
    'filters': {
        'remove_outliers': True,
        'outlier_sigma': 3.0,            # drop points > N stdev from local median
        'min_voltage_mv': 0.5,
        'max_rho_ratio': 10.0,           # drop points with rho_a/median > this
        'reciprocal_filter': True,
        'max_reciprocal_err_pct': 10.0,
        'min_quality_pct': 95.0,         # fail processing if clean data < X%
    },
    # ---------- MASW Dispersion ----------
    'masw': {
        'freq_min_hz': 5.0,              # ignore picks below this frequency
        'freq_max_hz': 35.0,             # ignore picks above this (aliasing zone)
        'auto_detect_fmax': True,        # auto-cut where SNR drops
        'snr_threshold': 0.3,            # mask zones where normalized energy < this
        'max_pick_jump_pct': 20.0,       # reject picks that jump > N% between adjacent f
        'smoothness_window': 3,          # moving-median window for picks
        'min_vs': 80.0,                  # m/s - plausibility lower bound
        'max_vs': 2500.0,                # m/s - plausibility upper bound
        'confirm_picker_before_vs': True,  # open interactive picker window
        'colormap': 'viridis',           # dispersion image colormap (override global)
    },
    # ---------- QC Display ----------
    'qc': {
        'show_rms_in_title': True,
        'show_iterations_in_title': True,
        'show_doi_line': True,
        'show_chi2': False,
        'show_electrode_positions_inverted': True,
        'remove_duplicate_titles': True,
        'include_qc_in_pdf': False,      # only when user presses the button
        'show_sensitivity_overlay': False,
    },
    # ---------- Confirmation ----------
    'confirmation': {
        'confirm_before_processing': True,
        'show_data_preview': True,
        'confirm_electrode_positions': True,
        'confirm_data_range': True,
        'confirm_file_count': True,
        'warn_on_low_quality': True,
    },
}

# Presets for quick DPI selection
IMAGE_PRESETS = {
    'Screen / Web (150)':      {'dpi': 150, 'fig_width': 12, 'fig_height': 8},
    'Print A4 (300)':          {'dpi': 300, 'fig_width': 14, 'fig_height': 9},
    'Journal / Thesis (600)':  {'dpi': 600, 'fig_width': 14, 'fig_height': 9},
    'Poster / Large (1200)':   {'dpi': 1200, 'fig_width': 16, 'fig_height': 10},
}

ARRAY_TYPES = {
    'wenner':         'Wenner (alpha) — classic 4-electrode, equal spacing',
    'schlumberger':   'Schlumberger — vertical sounding, high resolution',
    'dipole_dipole':  'Dipole-Dipole — best for lateral variations, deeper',
    'pole_dipole':    'Pole-Dipole — asymmetric, 1 remote electrode',
    'pole_pole':      'Pole-Pole — 2 remote electrodes, max depth',
    'wenner_schlumb': 'Wenner-Schlumberger — hybrid, balanced resolution',
}

INVERSION_METHODS = {
    'smoothness':  'Smoothness-constrained (Occam) — smooth, best for gradual changes',
    'robust':      'Robust (L1 norm) — sharp boundaries, resistant to outliers',
    'marquardt':   'Marquardt (ridge-regression) — damped least squares, stable',
}

MESH_FINENESS = {
    2: 'Coarse (fast, lower resolution)',
    4: 'Standard (balanced — recommended)',
    6: 'Fine (slower, higher resolution)',
    8: 'Very Fine (slow, max resolution)',
}


# ===================================================================
# Config helpers
# ===================================================================
def _deep_merge(base, override):
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load():
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        return _deep_merge(DEFAULTS, cfg)
    except (FileNotFoundError, json.JSONDecodeError):
        return {k: dict(v) for k, v in DEFAULTS.items()}


def save(cfg):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


# ===================================================================
# Apply (image settings only — inversion/filter settings are read
# by processing code at run-time via get() helpers below)
# ===================================================================
def apply_image(img_cfg):
    matplotlib.rcParams.update({
        'savefig.dpi':         img_cfg['dpi'],
        'figure.dpi':          min(120, img_cfg['dpi']),
        'figure.figsize':      (img_cfg['fig_width'], img_cfg['fig_height']),
        'savefig.format':      img_cfg['img_format'],
        'savefig.bbox':        'tight' if img_cfg['tight_layout'] else 'standard',
        'savefig.pad_inches':  0.15,
        'savefig.transparent': img_cfg['transparent'],
        'font.size':           img_cfg['font_size'],
        'axes.titlesize':      img_cfg['font_size'] + 2,
        'axes.titleweight':    'bold',
        'axes.labelsize':      img_cfg['font_size'],
        'xtick.labelsize':     img_cfg['font_size'] - 1,
        'ytick.labelsize':     img_cfg['font_size'] - 1,
        'legend.fontsize':     img_cfg['font_size'] - 1,
        'figure.titlesize':    img_cfg['font_size'] + 4,
        'image.cmap':          img_cfg['colormap'],
        'axes.grid':           True,
        'grid.alpha':          0.3,
        'grid.linestyle':      '--',
    })
    if img_cfg['force_dpi']:
        _patch_savefig(img_cfg['dpi'])


def apply(cfg):
    """Apply all applicable settings to the matplotlib runtime."""
    apply_image(cfg['image'])


def _patch_savefig(target_dpi):
    import matplotlib.figure
    import matplotlib.pyplot as plt
    if not hasattr(matplotlib.figure.Figure, '_seem_orig_savefig'):
        matplotlib.figure.Figure._seem_orig_savefig = matplotlib.figure.Figure.savefig
    if not hasattr(plt, '_seem_orig_savefig'):
        plt._seem_orig_savefig = plt.savefig

    _orig_fig = matplotlib.figure.Figure._seem_orig_savefig
    _orig_plt = plt._seem_orig_savefig

    def _enforce(kwargs):
        passed = kwargs.get('dpi')
        if passed is None or (isinstance(passed, (int, float)) and passed < target_dpi):
            kwargs['dpi'] = target_dpi
        kwargs.setdefault('bbox_inches', 'tight')
        kwargs.setdefault('pad_inches', 0.15)
        return kwargs

    def _hires_fig(self, *args, **kwargs):
        return _orig_fig(self, *args, **_enforce(kwargs))

    def _hires_plt(*args, **kwargs):
        return _orig_plt(*args, **_enforce(kwargs))

    matplotlib.figure.Figure.savefig = _hires_fig
    plt.savefig = _hires_plt


# Public getters used by processing modules
def get_inversion():  return load()['inversion']
def get_filters():    return load()['filters']
def get_masw():       return load()['masw']
def get_qc():         return load()['qc']
def get_confirmation(): return load()['confirmation']
def get_image():      return load()['image']


# Auto-apply at import
try:
    apply(load())
except Exception as e:
    print(f'[settings] WARNING: could not apply settings: {e}')


# ===================================================================
# Dialog
# ===================================================================
def show_dialog(parent=None):
    cfg = load()
    result = {'saved': None}

    standalone = parent is None
    root = tk.Tk() if standalone else tk.Toplevel(parent)
    root.title('⚙️  SEEM Geo — Settings')
    root.geometry('650x720')
    root.minsize(620, 700)
    if parent is not None:
        root.transient(parent)
        root.grab_set()

    BG, PANEL, ACCENT, MUTED = '#F5F5F5', '#FFFFFF', '#1F4E79', '#6B7280'
    root.configure(bg=BG)

    # Header
    hdr = tk.Frame(root, bg=ACCENT, height=56)
    hdr.pack(fill=tk.X); hdr.pack_propagate(False)
    tk.Label(hdr, text='⚙️  SEEM Geo Settings',
             font=('Segoe UI', 14, 'bold'),
             bg=ACCENT, fg='white').pack(side=tk.LEFT, padx=20, pady=14)
    tk.Label(hdr, text='Image · Inversion · Filters · QC · Confirmation',
             font=('Segoe UI', 9), bg=ACCENT, fg='#D1D5DB').pack(side=tk.LEFT, pady=18)

    # Tabs
    style = ttk.Style()
    try: style.theme_use('clam')
    except tk.TclError: pass
    style.configure('TNotebook.Tab', padding=[14, 7])

    nb = ttk.Notebook(root)
    nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))

    # Variable store — grouped by section
    vars = {sec: {} for sec in DEFAULTS}
    for sec, params in cfg.items():
        for k, v in params.items():
            if isinstance(v, bool):
                vars[sec][k] = tk.BooleanVar(value=v)
            elif isinstance(v, int):
                vars[sec][k] = tk.IntVar(value=v)
            elif isinstance(v, float):
                vars[sec][k] = tk.DoubleVar(value=v)
            else:
                vars[sec][k] = tk.StringVar(value=v)

    # --- Helper to build sections ---
    def mk_tab(title):
        f = tk.Frame(nb, bg=BG)
        nb.add(f, text=title)
        # Scrollable content
        canvas = tk.Canvas(f, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(f, orient='vertical', command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG)
        inner.bind('<Configure>',
                    lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=inner, anchor='nw')
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        return inner

    def section(parent, title):
        s = tk.Frame(parent, bg=PANEL, highlightthickness=1, highlightbackground='#E5E7EB')
        s.pack(fill=tk.X, pady=5)
        tk.Label(s, text=title, font=('Segoe UI', 10, 'bold'),
                 bg=PANEL, fg=ACCENT).pack(anchor='w', padx=12, pady=(8, 4))
        return s

    def row_spin(parent, label, var, from_, to, inc, width=8, suffix=''):
        r = tk.Frame(parent, bg=PANEL); r.pack(fill=tk.X, padx=12, pady=4)
        tk.Label(r, text=label, font=('Segoe UI', 9),
                 bg=PANEL, width=28, anchor='w').pack(side=tk.LEFT)
        tk.Spinbox(r, from_=from_, to=to, increment=inc, textvariable=var,
                    width=width, font=('Segoe UI', 10)).pack(side=tk.LEFT)
        if suffix:
            tk.Label(r, text=f'  {suffix}', font=('Segoe UI', 8),
                      bg=PANEL, fg=MUTED).pack(side=tk.LEFT, padx=4)

    def row_combo(parent, label, var, values, width=24):
        r = tk.Frame(parent, bg=PANEL); r.pack(fill=tk.X, padx=12, pady=4)
        tk.Label(r, text=label, font=('Segoe UI', 9),
                 bg=PANEL, width=28, anchor='w').pack(side=tk.LEFT)
        ttk.Combobox(r, textvariable=var, values=values,
                      state='readonly', width=width).pack(side=tk.LEFT)

    def row_check(parent, text, var):
        tk.Checkbutton(parent, text=text, variable=var,
                        font=('Segoe UI', 9), bg=PANEL, anchor='w').pack(
                            anchor='w', padx=12, pady=2)

    # ===================================================================
    # TAB 1: IMAGE OUTPUT
    # ===================================================================
    tab1 = mk_tab('🖼️  Image Output')
    V = vars['image']

    s = section(tab1, '🎯  Quick preset')
    preset_var = tk.StringVar(value='Print A4 (300)')
    pf = tk.Frame(s, bg=PANEL); pf.pack(fill=tk.X, padx=12, pady=(0, 10))
    def apply_preset():
        p = IMAGE_PRESETS.get(preset_var.get())
        if p:
            V['dpi'].set(p['dpi'])
            V['fig_width'].set(p['fig_width'])
            V['fig_height'].set(p['fig_height'])
    ttk.Combobox(pf, textvariable=preset_var, values=list(IMAGE_PRESETS.keys()),
                  state='readonly', width=24).pack(side=tk.LEFT, padx=(0, 8))
    tk.Button(pf, text='Apply preset ▶', bg=ACCENT, fg='white', relief='flat',
               padx=10, pady=4, cursor='hand2', command=apply_preset).pack(side=tk.LEFT)

    s = section(tab1, '🖼️  Resolution')
    row_spin(s, 'DPI (dots per inch):', V['dpi'], 72, 2400, 50,
              suffix='300=print  600=journal  1200=poster')
    row_check(s, 'Force DPI on all plots (override hard-coded values)',
               V['force_dpi'])

    s = section(tab1, '📐  Figure size (inches)')
    row_spin(s, 'Width:', V['fig_width'], 4.0, 30.0, 0.5, width=6)
    row_spin(s, 'Height:', V['fig_height'], 3.0, 20.0, 0.5, width=6)

    s = section(tab1, '🔤  Typography')
    row_spin(s, 'Base font size:', V['font_size'], 6, 24, 1, width=5)

    s = section(tab1, '🎨  Color map')
    cmaps = ['viridis', 'plasma', 'magma', 'inferno', 'cividis',
             'jet', 'turbo', 'seismic', 'RdYlBu_r', 'Spectral_r',
             'coolwarm', 'rainbow', 'gist_earth', 'terrain']
    row_combo(s, 'Colormap:', V['colormap'], cmaps, width=18)

    s = section(tab1, '💾  Save options')
    row_combo(s, 'Format:', V['img_format'],
               ['png', 'pdf', 'svg', 'jpg', 'tiff'], width=10)
    row_check(s, 'Tight bounding box (crop whitespace)', V['tight_layout'])
    row_check(s, 'Transparent background', V['transparent'])

    # ===================================================================
    # TAB 2: INVERSION
    # ===================================================================
    tab2 = mk_tab('⚡  Inversion')
    V = vars['inversion']

    s = section(tab2, '📡  Data type (electrode array)')
    row_combo(s, 'Array configuration:', V['array_type'],
               list(ARRAY_TYPES.keys()), width=20)
    tk.Label(s, text='ℹ️  Choose the array geometry used in the field.',
             font=('Segoe UI', 8), bg=PANEL, fg=MUTED,
             wraplength=560, justify='left').pack(anchor='w', padx=12, pady=(0, 10))

    s = section(tab2, '🔲  Mesh fineness (grid resolution)')
    row_combo(s, 'Mesh density:', V['mesh_fineness'],
               list(MESH_FINENESS.keys()), width=10)
    tk.Label(s, text='2=Coarse (fast)  ·  4=Standard  ·  6=Fine  ·  8=Very Fine (slow)',
             font=('Segoe UI', 8), bg=PANEL, fg=MUTED).pack(
                 anchor='w', padx=12, pady=(0, 10))

    s = section(tab2, '🔄  Inversion method')
    row_combo(s, 'Algorithm:', V['method'],
               list(INVERSION_METHODS.keys()), width=20)
    tk.Label(s,
             text='• smoothness: smooth gradual (Occam)\n'
                  '• robust: sharp boundaries (L1 norm)\n'
                  '• marquardt: damped least squares',
             font=('Segoe UI', 8), bg=PANEL, fg=MUTED,
             justify='left').pack(anchor='w', padx=12, pady=(0, 4))
    row_check(s, '🔬 Run ALL 3 methods and compare (slower × 3)',
               V['compare_methods'])

    s = section(tab2, '🎚️  Convergence parameters')
    row_spin(s, 'Max iterations:', V['max_iterations'], 3, 30, 1, width=5)
    row_spin(s, 'Target RMS error %:', V['target_rms_pct'], 1.0, 20.0, 0.5,
              width=5, suffix='< 5% is excellent, < 10% acceptable')
    row_spin(s, 'Damping factor (λ):', V['damping_factor'], 0.001, 1.0, 0.01, width=6)
    row_spin(s, 'H/V smoothness ratio:', V['h_v_smoothness_ratio'],
              0.1, 5.0, 0.1, width=5, suffix='1=equal, >1=horizontal bias')

    s = section(tab2, '🏔️  Advanced')
    row_check(s, 'Include topography correction', V['use_topography'])
    row_check(s, 'Apply wavelet filter to data', V['wavelet_filter'])

    # ===================================================================
    # TAB 3: DATA FILTERS
    # ===================================================================
    tab3 = mk_tab('🧹  Data Filters')
    V = vars['filters']

    s = section(tab3, '🚫  Outlier removal')
    row_check(s, 'Remove outliers before inversion',
               V['remove_outliers'])
    row_spin(s, 'Outlier threshold (σ):', V['outlier_sigma'], 1.0, 5.0, 0.1,
              width=5, suffix='points > N stdev from local median are dropped')
    row_spin(s, 'Max ρa / median ratio:', V['max_rho_ratio'],
              2.0, 50.0, 0.5, width=5, suffix='drop extreme spikes')

    s = section(tab3, '⚡  Signal quality')
    row_spin(s, 'Minimum voltage (mV):', V['min_voltage_mv'],
              0.01, 10.0, 0.1, width=6,
              suffix='readings below this are rejected')

    s = section(tab3, '🔁  Reciprocal check (if forward+reverse measured)')
    row_check(s, 'Enable reciprocal-error filter', V['reciprocal_filter'])
    row_spin(s, 'Max reciprocal error %:', V['max_reciprocal_err_pct'],
              1.0, 50.0, 0.5, width=5)

    s = section(tab3, '✅  Quality threshold')
    row_spin(s, 'Min clean-data %:', V['min_quality_pct'],
              50.0, 100.0, 1.0, width=5,
              suffix='warn if less than this % survives filtering')

    s = section(tab3, '💡 CLI equivalents')
    tk.Label(s,
             text='After editing here, these filters apply automatically to:\n'
                  '   python -m seem_geo ert <project.seemproj>\n'
                  '   python -m seem_geo pipeline <project.seemproj>\n'
                  'Or run manually:  python -m seem_geo filter-outliers <data.dat>',
             font=('Consolas', 8), bg=PANEL, fg=MUTED,
             justify='left').pack(anchor='w', padx=12, pady=(0, 10))

    # ===================================================================
    # TAB 3b: MASW DISPERSION (added as its own tab)
    # ===================================================================
    tab_masw = mk_tab('🌊  MASW Dispersion')
    V = vars['masw']

    s = section(tab_masw, '📊  Frequency band (dispersion picker limits)')
    row_spin(s, 'Min frequency (Hz):', V['freq_min_hz'], 1.0, 30.0, 0.5,
              width=6, suffix='below this, long-wavelength artifacts dominate')
    row_spin(s, 'Max frequency (Hz):', V['freq_max_hz'], 10.0, 200.0, 1.0,
              width=6, suffix='above this, aliasing / noise usually appears')
    row_check(s, 'Auto-detect fmax where SNR drops (recommended)',
               V['auto_detect_fmax'])

    s = section(tab_masw, '📶  Signal / noise filtering')
    row_spin(s, 'SNR mask threshold:', V['snr_threshold'], 0.05, 0.9, 0.05,
              width=6, suffix='mask zones with normalized energy < this')
    row_spin(s, 'Max adjacent-pick jump %:', V['max_pick_jump_pct'],
              5.0, 100.0, 5.0, width=6,
              suffix='reject picks jumping > N% between consecutive f-bins')
    row_spin(s, 'Smoothness window (f-bins):', V['smoothness_window'],
              1, 11, 1, width=5, suffix='moving-median smoothing of pick curve')

    s = section(tab_masw, '🚦  Plausibility bounds (Vs)')
    row_spin(s, 'Min Vs (m/s):', V['min_vs'], 50.0, 500.0, 10.0, width=6,
              suffix='reject picks below this (unrealistic soft layer)')
    row_spin(s, 'Max Vs (m/s):', V['max_vs'], 500.0, 5000.0, 50.0, width=6,
              suffix='reject picks above this (unrealistic hard layer)')

    s = section(tab_masw, '✋  Pre-inversion review')
    row_check(s, 'Open interactive picker review BEFORE Vs profile',
               V['confirm_picker_before_vs'])
    tk.Label(s,
             text='ℹ️  When ON, you can manually trim/re-pick the dispersion\n'
                  '    curve before it feeds the Vs inversion.',
             font=('Segoe UI', 8), bg=PANEL, fg=MUTED,
             justify='left').pack(anchor='w', padx=12, pady=(0, 10))

    s = section(tab_masw, '🎨  Dispersion image colormap')
    cmaps_m = ['viridis', 'plasma', 'magma', 'inferno', 'cividis',
                'jet', 'turbo', 'RdYlBu_r', 'Spectral_r']
    row_combo(s, 'MASW colormap:', V['colormap'], cmaps_m, width=16)
    tk.Label(s,
             text='⚠️  "jet" shows strong contrast but is perceptually non-uniform.\n'
                  '    "viridis" or "turbo" are better for scientific publication.',
             font=('Segoe UI', 8), bg=PANEL, fg=MUTED,
             justify='left').pack(anchor='w', padx=12, pady=(0, 10))

    # ===================================================================
    # TAB 4: QC DISPLAY
    # ===================================================================
    tab4 = mk_tab('📊  QC Display')
    V = vars['qc']

    s = section(tab4, '📏  Quality metrics on plots')
    row_check(s, 'Show RMS error in plot title', V['show_rms_in_title'])
    row_check(s, 'Show iteration count in plot title',
               V['show_iterations_in_title'])
    row_check(s, 'Draw DOI (Depth of Investigation) line',
               V['show_doi_line'])
    row_check(s, 'Show Chi² statistic', V['show_chi2'])
    row_check(s, 'Overlay sensitivity matrix (greyed-out low-sens zones)',
               V['show_sensitivity_overlay'])

    s = section(tab4, '🧹  Plot cleanup')
    row_check(s, 'Remove duplicate titles (keep matplotlib title only)',
               V['remove_duplicate_titles'])
    row_check(s, 'Mark electrode positions on inverted section',
               V['show_electrode_positions_inverted'])

    s = section(tab4, '📄  PDF report inclusion')
    row_check(s, 'Include QC panel in PDF report (toggle via Report button)',
               V['include_qc_in_pdf'])
    tk.Label(s,
             text='ℹ️  QC overlays always appear in the GUI preview.\n'
                  'They are embedded in the PDF only when this is ON\n'
                  'AND you press the "Include QC" button in the Report tab.',
             font=('Segoe UI', 8), bg=PANEL, fg=MUTED,
             justify='left').pack(anchor='w', padx=12, pady=(0, 10))

    # ===================================================================
    # TAB 5: CONFIRMATION
    # ===================================================================
    tab5 = mk_tab('✋  Confirmation')
    V = vars['confirmation']

    s = section(tab5, '📋  Pre-processing confirmation')
    row_check(s, 'Show confirmation dialog BEFORE processing starts',
               V['confirm_before_processing'])
    row_check(s, 'Display data-preview window (stations, counts, ranges)',
               V['show_data_preview'])

    s = section(tab5, '🔍  Items to verify')
    row_check(s, '✓ Electrode positions / spacing',
               V['confirm_electrode_positions'])
    row_check(s, '✓ Apparent-resistivity data range',
               V['confirm_data_range'])
    row_check(s, '✓ File count (expected vs found)',
               V['confirm_file_count'])

    s = section(tab5, '⚠️  Warnings')
    row_check(s, 'Warn when clean data < min_quality_pct',
               V['warn_on_low_quality'])

    s = section(tab5, 'ℹ️  How it works')
    tk.Label(s,
             text='Before each ERT or MASW run, SEEM Geo will:\n'
                  '  1. Load the raw files\n'
                  '  2. Apply the filters from the "Data Filters" tab\n'
                  '  3. Show you a summary (file count, data range, '
                  'rejected points)\n'
                  '  4. Wait for you to click "Confirm & Process" or "Cancel"\n'
                  '\nTurn this off for fully automated / scheduled runs.',
             font=('Segoe UI', 9), bg=PANEL, fg=MUTED,
             justify='left', wraplength=560).pack(
                 anchor='w', padx=12, pady=(0, 10))

    # ===================================================================
    # Buttons bar
    # ===================================================================
    btn_frame = tk.Frame(root, bg=BG)
    btn_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=12, pady=12)

    def collect_cfg():
        out = {}
        for sec in DEFAULTS:
            out[sec] = {}
            for k in DEFAULTS[sec]:
                v = vars[sec][k].get()
                # Normalize int-looking floats for mesh_fineness
                if k == 'mesh_fineness':
                    try: v = int(v)
                    except (ValueError, TypeError): v = 4
                out[sec][k] = v
        return out

    def on_apply(close=True):
        try:
            new = collect_cfg()
            save(new)
            apply(new)
            result['saved'] = new
            if close:
                messagebox.showinfo('Settings saved',
                                     f'All 5 tabs saved to:\n{CONFIG_PATH}\n\n'
                                     f'Image DPI: {new["image"]["dpi"]}\n'
                                     f'Inversion: {new["inversion"]["method"]} '
                                     f'(mesh={new["inversion"]["mesh_fineness"]})\n'
                                     f'Filters: outliers={"on" if new["filters"]["remove_outliers"] else "off"}\n'
                                     f'Confirm before run: '
                                     f'{"on" if new["confirmation"]["confirm_before_processing"] else "off"}',
                                     parent=root)
                root.destroy()
            else:
                messagebox.showinfo('Preview applied',
                                     'Settings applied for this session.\n'
                                     'Click OK + Save to persist.',
                                     parent=root)
        except Exception as e:
            messagebox.showerror('Error', str(e), parent=root)

    def on_reset():
        if messagebox.askyesno('Reset all tabs?',
                                 'Restore ALL 5 tabs to default values?\n'
                                 '(This affects image, inversion, filters, QC, '
                                 'confirmation.)', parent=root):
            for sec, params in DEFAULTS.items():
                for k, v in params.items():
                    try: vars[sec][k].set(v)
                    except Exception: pass

    tk.Button(btn_frame, text='Reset all', font=('Segoe UI', 10),
              bg='#E5E7EB', fg='#374151', relief='flat', padx=12, pady=6,
              cursor='hand2', command=on_reset).pack(side=tk.LEFT)
    tk.Button(btn_frame, text='Preview', font=('Segoe UI', 10),
              bg='#F3F4F6', fg='#374151', relief='flat', padx=12, pady=6,
              cursor='hand2', command=lambda: on_apply(False)).pack(side=tk.LEFT, padx=6)
    tk.Button(btn_frame, text='Cancel', font=('Segoe UI', 10),
              bg='#FEE2E2', fg='#991B1B', relief='flat', padx=12, pady=6,
              cursor='hand2', command=root.destroy).pack(side=tk.RIGHT, padx=4)
    tk.Button(btn_frame, text='OK + Save ✓', font=('Segoe UI', 10, 'bold'),
              bg=ACCENT, fg='white', relief='flat', padx=18, pady=6,
              cursor='hand2', command=lambda: on_apply(True)).pack(side=tk.RIGHT, padx=4)

    if standalone:
        root.mainloop()
    else:
        root.wait_window()
    return result['saved']


# ===================================================================
# Data-preview confirmation dialog (opens before processing)
# ===================================================================
def _find_data_dir(project, module):
    """Robustly locate the raw-data directory for ERT or MASW on any SeemProject version."""
    # Try common attribute names
    candidates = [
        f'{module}_raw_dir', f'{module}_data_dir',
        f'{module}_input_dir', f'{module}_raw',
    ]
    for attr in candidates:
        d = getattr(project, attr, None)
        if d and os.path.isdir(d):
            return d
    # Fallback: look under project.root in common locations
    root_dir = getattr(project, 'root', None) or os.getcwd()
    for sub in [f'data/{module}_raw', f'data/{module}', f'raw/{module}',
                 f'input/{module}', module]:
        candidate = os.path.join(root_dir, sub)
        if os.path.isdir(candidate):
            return candidate
    # Still nothing — return the expected default even if it doesn't exist yet
    return os.path.join(root_dir, 'data', f'{module}_raw')


def show_data_preview(parent, project, module='ert'):
    """
    Pre-processing confirmation dialog with EDITABLE settings inline.
    Returns True if user confirms, False if cancels.
    """
    conf = get_confirmation()
    if not conf.get('confirm_before_processing', True):
        return True

    import glob
    import traceback

    try:
        cfg = load()
    except Exception:
        cfg = {k: dict(v) for k, v in DEFAULTS.items()}

    BG, PANEL, ACCENT = '#F5F5F5', '#FFFFFF', '#1F4E79'
    OK_C, WARN_C, EDITED_C = '#10B981', '#F59E0B', '#2563EB'

    root = tk.Toplevel(parent) if parent else tk.Tk()
    root.title(f'Field Data Confirmation — {module.upper()}')
    root.geometry('780x780')
    root.minsize(720, 700)
    if parent:
        root.transient(parent); root.grab_set()
    root.configure(bg=BG)

    result = {'confirmed': False}
    confirmed = tk.BooleanVar(value=False)

    # Live tk variables for every editable setting
    edit_vars = {}
    def mk_var(section, key, is_bool=False, is_int=False, is_float=False):
        v = cfg[section][key]
        if is_bool:  tv = tk.BooleanVar(value=v)
        elif is_int:   tv = tk.IntVar(value=v)
        elif is_float: tv = tk.DoubleVar(value=v)
        else:          tv = tk.StringVar(value=str(v))
        edit_vars[(section, key)] = tv
        return tv

    # Header
    h = tk.Frame(root, bg=ACCENT, height=50); h.pack(fill=tk.X); h.pack_propagate(False)
    tk.Label(h, text=f'Confirm field data before {module.upper()} processing',
             font=('Segoe UI', 12, 'bold'), bg=ACCENT, fg='white').pack(
                 side=tk.LEFT, padx=16, pady=12)
    tk.Label(h, text='✎ edit any value below', font=('Segoe UI', 9),
             bg=ACCENT, fg='#CBD5E1').pack(side=tk.LEFT, pady=16)

    # Button bar at bottom
    def do_confirm():
        if not confirmed.get():
            messagebox.showwarning('Please confirm',
                                     'Tick the review checkbox first.',
                                     parent=root)
            return
        # Save edited values back to settings file
        try:
            saved = load()
            for (sec, key), tv in edit_vars.items():
                val = tv.get()
                if key == 'mesh_fineness':
                    try: val = int(val)
                    except (ValueError, TypeError): val = 4
                saved[sec][key] = val
            save(saved)
            apply(saved)
        except Exception as e:
            messagebox.showerror('Save error', f'Could not save settings: {e}',
                                   parent=root)
            return
        result['confirmed'] = True
        root.destroy()

    def do_cancel():
        root.destroy()

    btn = tk.Frame(root, bg=BG); btn.pack(fill=tk.X, side=tk.BOTTOM, padx=12, pady=12)
    tk.Button(btn, text='✓ Save & Process', font=('Segoe UI', 10, 'bold'),
              bg=OK_C, fg='white', relief='flat', padx=18, pady=8,
              cursor='hand2', command=do_confirm).pack(side=tk.RIGHT, padx=4)
    tk.Button(btn, text='Cancel', font=('Segoe UI', 10),
              bg='#FEE2E2', fg='#991B1B', relief='flat', padx=18, pady=8,
              cursor='hand2', command=do_cancel).pack(side=tk.RIGHT, padx=4)
    tk.Button(btn, text='⚙ Full Settings', font=('Segoe UI', 10),
              bg='#F3F4F6', fg='#374151', relief='flat', padx=12, pady=8,
              cursor='hand2',
              command=lambda: show_dialog(root)).pack(side=tk.LEFT)

    # Confirm checkbox above buttons
    cf = tk.Frame(root, bg=BG); cf.pack(fill=tk.X, side=tk.BOTTOM, padx=16, pady=(10, 0))
    tk.Checkbutton(cf,
                    text='I have reviewed the data and settings — proceed',
                    variable=confirmed, font=('Segoe UI', 10, 'bold'),
                    bg=BG).pack(anchor='w')

    # Scrollable body
    body_frame = tk.Frame(root, bg=BG)
    body_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)
    canvas = tk.Canvas(body_frame, bg=BG, highlightthickness=0)
    sb = ttk.Scrollbar(body_frame, orient='vertical', command=canvas.yview)
    body = tk.Frame(canvas, bg=BG)
    body.bind('<Configure>',
               lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.create_window((0, 0), window=body, anchor='nw', width=720)
    canvas.configure(yscrollcommand=sb.set)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.pack(side=tk.RIGHT, fill=tk.Y)
    # Mouse wheel
    def _mw(e):
        canvas.yview_scroll(int(-1 * (e.delta / 120)), 'units')
    canvas.bind_all('<MouseWheel>', _mw)

    def panel(title):
        p = tk.Frame(body, bg=PANEL, highlightthickness=1,
                      highlightbackground='#E5E7EB')
        p.pack(fill=tk.X, pady=4, padx=4)
        tk.Label(p, text=title, font=('Segoe UI', 10, 'bold'),
                 bg=PANEL, fg=ACCENT).pack(anchor='w', padx=12, pady=(10, 6))
        return p

    def info_row(parent, label, value, status=None):
        r = tk.Frame(parent, bg=PANEL); r.pack(fill=tk.X, padx=12, pady=2)
        color = {'ok': OK_C, 'warn': WARN_C}.get(status, '#374151')
        icon = {'ok': '✓ ', 'warn': '⚠ '}.get(status, '  ')
        tk.Label(r, text=f'{icon}{label}', font=('Segoe UI', 9),
                 bg=PANEL, fg=color, width=28, anchor='w').pack(side=tk.LEFT)
        tk.Label(r, text=str(value), font=('Segoe UI', 9, 'bold'),
                 bg=PANEL, fg=color, wraplength=440,
                 justify='left').pack(side=tk.LEFT, fill=tk.X, expand=True)

    def edit_spin(parent, label, var, from_, to, inc, width=8, suffix=''):
        r = tk.Frame(parent, bg=PANEL); r.pack(fill=tk.X, padx=12, pady=3)
        tk.Label(r, text=f'✎ {label}', font=('Segoe UI', 9),
                 bg=PANEL, fg=EDITED_C, width=28, anchor='w').pack(side=tk.LEFT)
        tk.Spinbox(r, from_=from_, to=to, increment=inc, textvariable=var,
                    width=width, font=('Segoe UI', 10)).pack(side=tk.LEFT)
        if suffix:
            tk.Label(r, text=f'  {suffix}', font=('Segoe UI', 8),
                      bg=PANEL, fg='#6B7280').pack(side=tk.LEFT, padx=4)

    def edit_combo(parent, label, var, values, width=20):
        r = tk.Frame(parent, bg=PANEL); r.pack(fill=tk.X, padx=12, pady=3)
        tk.Label(r, text=f'✎ {label}', font=('Segoe UI', 9),
                 bg=PANEL, fg=EDITED_C, width=28, anchor='w').pack(side=tk.LEFT)
        ttk.Combobox(r, textvariable=var, values=values,
                      state='readonly', width=width).pack(side=tk.LEFT)

    def edit_check(parent, label, var):
        r = tk.Frame(parent, bg=PANEL); r.pack(fill=tk.X, padx=12, pady=2)
        tk.Checkbutton(r, text=f'✎ {label}', variable=var,
                        font=('Segoe UI', 9), bg=PANEL,
                        fg=EDITED_C).pack(anchor='w')

    # ------------------- Build body -------------------
    try:
        # Project info (read-only)
        try:
            n_sites = len(getattr(project, 'sites', []))
        except Exception:
            n_sites = 0
        try:
            proj_name = project.summary().get('name', 'Unknown')
        except Exception:
            proj_name = str(getattr(project, 'name', 'Unknown'))

        data_dir = _find_data_dir(project, module)
        try:
            files = sorted(glob.glob(os.path.join(data_dir, '*'))) \
                if os.path.isdir(data_dir) else []
        except Exception:
            files = []
        n_files = len(files)

        p = panel('📂 Dataset summary (read-only)')
        info_row(p, 'Project:', proj_name)
        info_row(p, 'Sites configured:', n_sites,
                  'ok' if n_sites > 0 else 'warn')
        info_row(p, 'Data files found:', n_files,
                  'ok' if n_files >= n_sites and n_sites > 0 else 'warn')
        info_row(p, 'Data folder exists:',
                  'YES' if os.path.isdir(data_dir) else 'NO (will skip)',
                  'ok' if os.path.isdir(data_dir) else 'warn')
        info_row(p, 'Path:', data_dir)
        tk.Frame(p, bg=PANEL, height=8).pack()

        # ---------- Editable: Filters ----------
        p = panel('🧹 Data filters (editable)')
        edit_check(p, 'Remove outliers before processing',
                    mk_var('filters', 'remove_outliers', is_bool=True))
        edit_spin(p, 'Outlier threshold (σ):',
                   mk_var('filters', 'outlier_sigma', is_float=True),
                   1.0, 5.0, 0.1, width=5, suffix='standard deviations')
        edit_check(p, 'Enable reciprocal filter',
                    mk_var('filters', 'reciprocal_filter', is_bool=True))
        edit_spin(p, 'Min voltage (mV):',
                   mk_var('filters', 'min_voltage_mv', is_float=True),
                   0.01, 10.0, 0.1, width=5)
        edit_spin(p, 'Min quality %:',
                   mk_var('filters', 'min_quality_pct', is_float=True),
                   50.0, 100.0, 1.0, width=5)
        tk.Frame(p, bg=PANEL, height=8).pack()

        # ---------- Module-specific ----------
        if module == 'ert':
            p = panel('⚡ ERT Inversion (editable)')
            edit_combo(p, 'Array type:',
                        mk_var('inversion', 'array_type'),
                        list(ARRAY_TYPES.keys()), width=18)
            edit_combo(p, 'Inversion method:',
                        mk_var('inversion', 'method'),
                        list(INVERSION_METHODS.keys()), width=18)
            edit_check(p, 'Compare ALL 3 methods (slower × 3)',
                        mk_var('inversion', 'compare_methods', is_bool=True))
            edit_combo(p, 'Mesh fineness:',
                        mk_var('inversion', 'mesh_fineness', is_int=True),
                        [2, 4, 6, 8], width=8)
            edit_spin(p, 'Max iterations:',
                       mk_var('inversion', 'max_iterations', is_int=True),
                       3, 30, 1, width=5)
            edit_spin(p, 'Target RMS %:',
                       mk_var('inversion', 'target_rms_pct', is_float=True),
                       1.0, 20.0, 0.5, width=5,
                       suffix='<5% excellent, <10% acceptable')
            edit_spin(p, 'Damping (λ):',
                       mk_var('inversion', 'damping_factor', is_float=True),
                       0.001, 1.0, 0.01, width=6)
            edit_spin(p, 'H/V smoothness ratio:',
                       mk_var('inversion', 'h_v_smoothness_ratio',
                               is_float=True),
                       0.1, 5.0, 0.1, width=5)
            edit_check(p, 'Include topography correction',
                        mk_var('inversion', 'use_topography', is_bool=True))
            tk.Frame(p, bg=PANEL, height=8).pack()
        else:  # masw
            p = panel('🌊 MASW Dispersion (editable)')
            edit_spin(p, 'Min frequency (Hz):',
                       mk_var('masw', 'freq_min_hz', is_float=True),
                       1.0, 30.0, 0.5, width=6)
            edit_spin(p, 'Max frequency (Hz):',
                       mk_var('masw', 'freq_max_hz', is_float=True),
                       10.0, 200.0, 1.0, width=6,
                       suffix='cut aliasing/noise zone')
            edit_check(p, 'Auto-detect fmax from SNR',
                        mk_var('masw', 'auto_detect_fmax', is_bool=True))
            edit_spin(p, 'SNR mask threshold:',
                       mk_var('masw', 'snr_threshold', is_float=True),
                       0.05, 0.9, 0.05, width=5)
            edit_spin(p, 'Max pick jump %:',
                       mk_var('masw', 'max_pick_jump_pct', is_float=True),
                       5.0, 100.0, 5.0, width=5)
            edit_spin(p, 'Smoothness window:',
                       mk_var('masw', 'smoothness_window', is_int=True),
                       1, 11, 1, width=4, suffix='f-bins (moving median)')
            edit_spin(p, 'Min Vs (m/s):',
                       mk_var('masw', 'min_vs', is_float=True),
                       50.0, 500.0, 10.0, width=6)
            edit_spin(p, 'Max Vs (m/s):',
                       mk_var('masw', 'max_vs', is_float=True),
                       500.0, 5000.0, 50.0, width=6)
            edit_check(p, 'Open interactive picker before Vs inversion',
                        mk_var('masw', 'confirm_picker_before_vs',
                                is_bool=True))
            edit_combo(p, 'Dispersion colormap:',
                        mk_var('masw', 'colormap'),
                        ['viridis', 'plasma', 'turbo', 'jet',
                         'RdYlBu_r', 'Spectral_r', 'magma'], width=14)
            tk.Frame(p, bg=PANEL, height=8).pack()

        # ---------- Image output quick controls ----------
        p = panel('🖼️ Image output (editable)')
        edit_spin(p, 'DPI:',
                   mk_var('image', 'dpi', is_int=True),
                   72, 2400, 50, width=6,
                   suffix='300=print  600=journal  1200=poster')
        edit_combo(p, 'Colormap:',
                    mk_var('image', 'colormap'),
                    ['viridis', 'plasma', 'turbo', 'jet',
                     'RdYlBu_r', 'Spectral_r', 'magma', 'cividis'],
                    width=14)
        edit_combo(p, 'Format:',
                    mk_var('image', 'img_format'),
                    ['png', 'pdf', 'svg', 'jpg', 'tiff'], width=8)
        tk.Frame(p, bg=PANEL, height=8).pack()

        # Warnings
        if n_sites == 0:
            w = tk.Frame(body, bg='#FEF3C7', highlightthickness=1,
                          highlightbackground=WARN_C)
            w.pack(fill=tk.X, pady=4, padx=4)
            tk.Label(w, text='⚠ No sites configured — add sites first.',
                      font=('Segoe UI', 9), bg='#FEF3C7', fg='#92400E'
                      ).pack(padx=12, pady=10)
        elif n_files == 0:
            w = tk.Frame(body, bg='#FEF3C7', highlightthickness=1,
                          highlightbackground=WARN_C)
            w.pack(fill=tk.X, pady=4, padx=4)
            tk.Label(w, text=f'⚠ No data files in: {data_dir}\n'
                              'Run "Generate data" first or copy files there.',
                      font=('Segoe UI', 9), bg='#FEF3C7', fg='#92400E',
                      justify='left').pack(padx=12, pady=10)
        elif n_files < n_sites:
            w = tk.Frame(body, bg='#FEF3C7', highlightthickness=1,
                          highlightbackground=WARN_C)
            w.pack(fill=tk.X, pady=4, padx=4)
            tk.Label(w, text=f'⚠ Only {n_files} files for {n_sites} sites — '
                              f'missing stations will be skipped.',
                      font=('Segoe UI', 9), bg='#FEF3C7', fg='#92400E'
                      ).pack(padx=12, pady=10)

    except Exception as e:
        err = tk.Frame(body, bg='#FEE2E2', highlightthickness=1,
                        highlightbackground='#DC2626')
        err.pack(fill=tk.X, pady=4, padx=4)
        tk.Label(err,
                  text=f'Error:\n{e}\n\n{traceback.format_exc()[-400:]}',
                  font=('Consolas', 8), bg='#FEE2E2', fg='#991B1B',
                  wraplength=680, justify='left').pack(padx=12, pady=10)

    root.wait_window()
    return result['confirmed']


# ===================================================================
# QC-overlay helper (used by processing code to format plot titles)
# ===================================================================
def format_plot_title(base_title, rms=None, iterations=None, chi2=None, doi=None):
    """Build a plot title that respects the user's QC display settings."""
    q = get_qc()
    parts = [base_title]
    extras = []
    if q.get('show_rms_in_title') and rms is not None:
        extras.append(f'RMS={rms:.1f}%')
    if q.get('show_iterations_in_title') and iterations is not None:
        extras.append(f'{iterations} iter')
    if q.get('show_chi2') and chi2 is not None:
        extras.append(f'χ²={chi2:.2f}')
    if q.get('show_doi_line') and doi is not None:
        extras.append(f'DOI={doi:.1f}m')
    if extras:
        parts.append(f"({', '.join(extras)})")
    return '  '.join(parts)


if __name__ == '__main__':
    saved = show_dialog()
    if saved:
        print(f'[settings] Saved to {CONFIG_PATH}')
    else:
        print('[settings] Cancelled.')
