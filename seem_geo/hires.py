"""
seem_geo/hires.py — Force high-resolution image output for SEEM Geo.

Usage:
    import seem_geo.hires        # apply patch
    from seem_geo.gui.pro_main_window import main
    main()

Or on the command line:
    python -c "import seem_geo.hires; from seem_geo.gui.pro_main_window import main; main()"

Effect:
    All matplotlib savefig() calls produced during this Python session
    (ERT, MASW, fence, correlations, Vs30, PDF plots) are forced to 300 DPI
    with a tight bounding box. Font sizes and figure dimensions are also
    nudged up so text stays legible at high DPI.
"""
import matplotlib
import matplotlib.figure
import matplotlib.pyplot as plt

# -------------------------------------------------------------------
# Tune these three to taste
# -------------------------------------------------------------------
TARGET_DPI    = 300          # 300 = publication / A4 print, 600 = journal
INTERACT_DPI  = 120          # on-screen rendering (higher = sharper preview)
TARGET_FIGSIZE = (14, 9)     # inches, width x height

# -------------------------------------------------------------------
# 1) Global rcParams — baseline for every new figure
# -------------------------------------------------------------------
matplotlib.rcParams.update({
    'savefig.dpi':         TARGET_DPI,
    'figure.dpi':          INTERACT_DPI,
    'savefig.bbox':        'tight',
    'savefig.pad_inches':  0.15,
    'figure.figsize':      TARGET_FIGSIZE,

    # typography — scaled up so 300-DPI prints are still legible
    'font.family':         'DejaVu Sans',
    'font.size':           11,
    'axes.titlesize':      13,
    'axes.titleweight':    'bold',
    'axes.labelsize':      11,
    'xtick.labelsize':     10,
    'ytick.labelsize':     10,
    'legend.fontsize':     10,
    'figure.titlesize':    15,
    'figure.titleweight':  'bold',

    # grid + colormap
    'image.cmap':          'viridis',
    'axes.grid':           True,
    'grid.alpha':          0.3,
    'grid.linestyle':      '--',
    'grid.linewidth':      0.5,

    # colorbar
    'axes.axisbelow':      True,
    'axes.linewidth':      1.0,

    # line weights
    'lines.linewidth':     1.5,
    'patch.linewidth':     1.0,

    # saving
    'savefig.format':      'png',
    'savefig.transparent': False,
})

# -------------------------------------------------------------------
# 2) Monkey-patch savefig — enforce TARGET_DPI even if the code inside
#    seem_geo hard-codes a lower value (e.g. dpi=100). Any explicit
#    value >= TARGET_DPI is left alone, so dpi=600 keeps winning.
# -------------------------------------------------------------------
_orig_fig_savefig = matplotlib.figure.Figure.savefig
_orig_plt_savefig = plt.savefig


def _enforce_dpi(kwargs):
    passed = kwargs.get('dpi')
    if passed is None or (isinstance(passed, (int, float)) and passed < TARGET_DPI):
        kwargs['dpi'] = TARGET_DPI
    kwargs.setdefault('bbox_inches', 'tight')
    kwargs.setdefault('pad_inches', 0.15)
    return kwargs


def _hires_fig_savefig(self, *args, **kwargs):
    kwargs = _enforce_dpi(kwargs)
    return _orig_fig_savefig(self, *args, **kwargs)


def _hires_plt_savefig(*args, **kwargs):
    kwargs = _enforce_dpi(kwargs)
    return _orig_plt_savefig(*args, **kwargs)


matplotlib.figure.Figure.savefig = _hires_fig_savefig
plt.savefig = _hires_plt_savefig

print(f'[hires] SEEM Geo image output set to {TARGET_DPI} DPI '
      f'(figure {TARGET_FIGSIZE[0]}x{TARGET_FIGSIZE[1]} in).')
