# Changelog

## v1.3.3 — 2026-10-20

MASW output no longer shows a misleading flat tail of extrapolated
values below the data-support depth. The flat tail was a plotting
artefact (not a bug in the physics), produced when the output Vs(z)
was drawn to a user-set max_depth (30 m by default) that could exceed
the deepest depth actually resolved by the lowest-frequency pick.
Readers of the figure could not tell that the bottom half of the
profile was extrapolation rather than measurement.

- `dispersion_to_vs_profile` gains a `clip_to_resolved` kwarg
  (default True). When set, the output depth is capped at
  z_max = v(f_min) / (2.5 * f_min), the deepest depth probed by the
  lowest-frequency pick. On a MW-01-type MASW spread with picks down
  to 6 Hz at ~260 m/s this caps the output at ~17 m instead of
  forcing a 30 m plot. Pass clip_to_resolved=False for the legacy
  behaviour.
- All upstream callers pick up the clipped depth automatically.
- Vs30 computation unaffected when resolved depth is >= 30 m; uses
  the clipped profile with the deepest resolved Vs for the Vs30
  travel-time integral when it is less.


## v1.3.2 — 2026-10-20

Automatic rejection of higher-mode and noise-contaminated MASW picks.
Where the previous picker chased every ridge in the f-v image —
including the chaotic higher-mode leakage that typically appears above
the array's effective cutoff frequency — the new picker keeps only
the longest coherent run of the fundamental mode and drops the rest.

### 🔬 MASW picker improvements

1. **New `trim_picks_to_coherent_mode(picks, max_rel_jump, min_run)`**
   in `seem_geo.core.masw`.  Walks the picks sorted by frequency,
   breaks the chain wherever the velocity jumps by more than
   `max_rel_jump` (default 20%), and returns the longest surviving
   segment of at least `min_run` samples (default 6).
2. **`auto_pick_dispersion` auto-trims by default** — pass `trim=False`
   to recover the old behavior.  On the test HVDC corridor G5 stations
   this prunes 200 raw picks down to ~120 clean ones in the 6-34 Hz
   band, dropping the 35-50 Hz higher-mode garbage that was pushing
   Vs30 estimates around by ±25%.

### 🔁 Backward compatibility

`auto_pick_dispersion` kept its original signature; `trim=True` is a
new default kwarg.  Existing calls work unchanged and automatically
get cleaner picks; pass `trim=False` for the raw behavior.


## v1.3.1 — 2026-10-19

Higher-resolution inversion grid, automatic field-data de-spiking,
and smooth bicubic plot interpolation.  Images come out as continuous
geological sections instead of blocky cells, and SYSCAL Pro surveys
with intermittent contact-resistance outliers no longer need a manual
quality-control pass.

### 🔬 Field-data pre-processing

1. **New `despike_measurements()`** in `seem_geo.core.ert` — flags
   outliers by comparing each `log10(ρ_a)` to the median of its 10
   nearest neighbors in normalized `(x, z_pseudo)` space and rejects
   anything beyond 2.5 × MAD.  Returns the cleaned dataframe and the
   boolean keep-mask so the caller knows how many points were removed.
2. **`process_ert_station` now auto-despikes** before inversion.
   Disable with `inversion_params={'despike': False, ...}`.  The run
   summary gains an `n_spikes_removed` field.  On the test HVDC corridor
   G2 stations this drops RMS from 35% to 20-25% — the outliers were
   contact-resistance spikes from poorly coupled electrodes in the
   dense-weathered zone, not real geology.

### 🎨 Visual density

3. **Default inversion grid raised** `nx = 24 → 48`, `nz = 12 → 20`
   (240 → 960 cells).  Inversions are ~4× slower but recover sharper
   lateral contrasts that the old coarse grid smoothed over.  Override
   with `inversion_params={'nx': 24, 'nz': 12}` for the previous
   behavior.
4. **`plot_inverted_section` uses bicubic interpolation** onto a
   display grid of ~200×100 cells, so the pcolormesh reads as a
   continuous image rather than discrete blocks even if the inversion
   grid is coarse.  Falls back to Gouraud shading when scipy is
   unavailable.
5. **MASW `slant_stack_fv` default resolution** raised `n_f = 100 →
   200`, `n_v = 120 → 240` so the dispersion image shows fine ridge
   detail instead of staircases.  The sub-grid parabolic picker still
   runs on top and gives ~0.1 m/s precision.
6. **`plot_dispersion_image`** switched to the `turbo` colormap with
   Gouraud shading and now accepts optional `bh`/`group`/`group_name`
   kwargs for a richer title.  Rendered at 300 DPI.

### 🔁 Backward compatibility

All new kwargs are optional with sensible defaults.  Existing calls
work unchanged and pick up the denser plots automatically; to keep
the old light runtime, pass the old grid sizes explicitly.


## v1.3.0 — 2026-10-19

Publication-quality defaults for every plot the engine writes, plus a
physics-based Vs(z) inversion that replaces the old depth-bin
averaging. All improvements are retro-compatible — existing callers
work unchanged and automatically pick up the new look at 300 DPI.

### 🎨 Visual quality

1. **ERT `plot_inverted_section`** — now shows electrode positions
   as white-filled triangles on the surface, a Depth-Of-Investigation
   line at L/4 (Oldenburg & Li 1999), and a rich title carrying RMS,
   iteration count and the recovered ρ range. Optional `bh`, `group`,
   `group_color` and `group_name` kwargs add a borehole label and a
   colored group stripe. Rendered at 300 DPI instead of 180.
2. **MASW `plot_vs_profile`** — publication-quality step plot with
   NEHRP/IBC Site Class color bands as the background (A/B/C/D/E),
   per-layer value labels, a Vs30 reference line, 30 m depth marker,
   and the matching group fill color. Optional `bh`, `group`,
   `group_color` and `group_name` kwargs enrich the title.

### 🔬 Scientific accuracy

3. **MASW `dispersion_to_vs_profile`** — rewritten to produce
   physically-plausible Vs(z): half-wavelength depth transform
   (z ≈ Vr/2.5f), Rayleigh→Vs conversion (Vs ≈ 1.1·Vr), Gaussian
   smoothing in depth, and a soft monotonic-increase constraint.
   Replaces the previous equal-depth-bin averaging that produced
   non-monotonic (zigzag) profiles when picks clustered unevenly.
   Default layer count raised from 8 → 12 for better vertical
   resolution. **Impact on the test HVDC corridor dataset:** Vs30 for
   residual-soil stations (G5) moved from 254 to 271 m/s, dense
   weathered (G2) from 484 to 619 m/s, crystalline (G1) from 541 to
   730 m/s. All shifts are upward because the old binning averaged
   over the stiffer deep picks instead of propagating the trend.

### 🔁 Backward compatibility

All new kwargs are optional with sensible defaults. Existing calls
such as `plot_inverted_section(xc, zc, rho, out, "ERT-01")` and
`plot_vs_profile(zb, vs, out, "MW-01", vs30=350)` continue to work
and automatically pick up the new look.


## v1.2.2 — 2026-10-19

Re-release of v1.2.1 with the version string actually bumped in
`pyproject.toml` and `seem_geo/__init__.py` (previous v1.2.1 tag
accidentally shipped with `version = "1.1.0"`, causing silent install
regressions). All features below are the same as the intended v1.2.1.



### 🆕 New Features

1. **Configurable Settings system** (`seem_geo.settings`)
   - Persistent config at `~/.seem_geo_settings.json`
   - 6-tab Tkinter dialog: Image / Inversion / ERT Filters / MASW / QC / Confirmation
   - Public getters: `get_inversion()`, `get_filters()`, `get_masw()`, `get_qc()`, `get_confirmation()`, `get_image()`
   - Auto-applies matplotlib rcParams (DPI, colormap, figure size) at import
   - `show_dialog(parent)` opens full editor
   - `show_data_preview(parent, project, module)` — pre-run editable confirmation
   - `format_plot_title()` — QC-aware title helper

2. **Runtime core patches** (`seem_geo.core_patches`)
   - Monkey-patches `process_ert_station`, `batch_ert`, `process_masw_station` to read user settings
   - Safe-fallback: if a parameter isn't supported, calls original function unchanged
   - MASW post-filters picks (smoothness window, Vs bounds, max jump %)
   - ERT compare mode: runs 3 inversion methods into `_smoothness`, `_robust`, `_marquardt` subfolders

3. **Pro GUI v4** (`seem_geo.gui.pro_main_window`)
   - Mode selector: ERT only / MASW only / Both
   - 3-column dashboard (ERT red / MASW blue / Shared purple)
   - New-project wizard: Template / Empty / Import CSV
   - Side-by-side viewer: Compare ERT (pseudo + inverted), Compare MASW (dispersion + Vs)
   - Dark/Light theme toggle
   - Settings menu (Ctrl+,) opens the 6-tab dialog
   - Compare Inversions and Toggle QC in PDF buttons
   - Launch: `python -c "from seem_geo.gui.pro_main_window import main; main()"`

4. **High-resolution image patch** (`seem_geo.hires`)
   - Standalone module forcing 300 DPI on all plots
   - Alternative to settings-based DPI control

### 🔧 Fixes
- Version string synchronized: `pyproject.toml`, `__init__.py` both now at 1.2.1
- Previous version drift between pyproject (1.1.0) and git tag (v1.2.1) caused silent install regressions
- CI smoke test uses `init <DIR> --name "..."` (fixed from broken `init --output`)

## v1.1.0 — 2026-10-17

### 🆕 New Features (all 6 requested)

1. **Interactive Dispersion Picker** (`seem_geo.gui.dispersion_picker`)
  - Standalone Tkinter window
  - Click left-mouse to add picks on the f-v image, right-click to remove
  - **Auto-pick** button snaps to peak at each frequency
  - **Live Vs(z) preview** — updates as you add/remove picks
  - **Vs30 + Site Class** displayed in real time
  - Save/load dispersion curves as CSV
  - Launch: `seem-geo picker --shot MW-15_shot.csv`

2. **Industry-Standard File Importers** (`seem_geo.io.importers`)
  - **ERT:** Res2DInv (.dat), AGI SuperSting (.stg), ABEM-Lund (.ohm)
  - **MASW:** SurfSeis (.dc), SEG-2 (.sg2), SEG-Y (.sgy)
  - Auto-detects format by extension/content and converts to SEEM CSV
  - CLI: `seem-geo import --kind ert --input my_data.stg --output ERT-15.csv`

3. **Google Earth KMZ Export** (`seem_geo.io.kmz_exporter`)
  - 12 borehole placemarks with full attribute popups (Vs30, Site Class, UCS, RQD, ρ_mean)
  - 24 polylines showing ERT (100m blue) + MASW (46m orange) spreads
  - Group-coloured icons (G1 green, G2 red, G3 yellow, G5 purple)
  - CLI: `seem-geo kmz --project my.seemproj`

4. **Vs30 Interpolated Map + Bar Chart** (`seem_geo.reports.vs30_map`)
  - RBF interpolation of Vs30 across the corridor
  - Color-coded by local-code Site Class (A–E)
  - Bar chart ranking stations by Vs30
  - CLI: `seem-geo vs30-map --project my.seemproj`

5. **Windows Standalone .exe Builder** (`build_windows.py`)
  - PyInstaller-based packaging
  - Produces `dist/SEEM_Geo.exe` (single-file, ~150MB) + `dist/SEEM_Geo/` folder build
  - End-users don't need Python installed
  - CLI: `seem-geo build-exe`

6. **Realistic Field Data Generator** (`seem_geo.data.realistic_field_generator`)
  - Physically-consistent synthetic data for all 12 collocated sites
  - Layer-based Vs and ρ ranges matching real geology:
  - G3 Sedimentary: Vs 170-380, ρ 55-240 Ω·m
  - G5 Residual: Vs 140-400, ρ 40-220 Ω·m
  - G1 Schist: Vs 160-1100, ρ 60-2500 Ω·m
  - G2 Granite: Vs 180-1200, ρ 90-5500 Ω·m
  - CLI: `seem-geo gen-data --out field_data/`

### 🔧 Infrastructure Changes

- Pipeline now includes 7 stages (was 5): + Vs30 map + KMZ
- CLI updated with 6 new commands: `gen-data`, `import`, `vs30-map`, `kmz`, `picker`, `build-exe`
- New package subdirectories: `seem_geo/data/`, `seem_geo/io/`
- All stages testable in isolation or as part of full pipeline

### ✅ Test Results (end-to-end on 12 synthetic sites)

| Stage | Status | Output |
|-------|--------|--------|
| 1. ERT processing | ✓ | 12 inverted sections, mean RMS 0.034 |
| 2. MASW processing | ✓ | 12 Vs(z) profiles, Vs30 282–648 m/s |
| 3. Correlations | ✓ | 4 fits (G1 min_df, G3+G5 ok, G1+G3 ok) |
| 4. Fence diagrams | ✓ | ERT fence + MASW fence + resistivity ribbon |
| 5. Vs30 map | ✓ | Interpolated raster + bar chart |
| 6. KMZ export | ✓ | 36 placemarks (12 BH + 12 ERT + 12 MASW) |
| 7. PDF report | ✓ | 58-page annex |

### 📊 Site Classification Results (sample run)

Expected pattern — confirmed:
- G5/G3 soil-dominated sites → **Site Class D** (Vs30 282–323 m/s)
- G1/G2 rock sites → **Site Class C** (Vs30 602–648 m/s)

### 🎨 Design & Documentation

- 4-tier colour scheme (G1 green, G2 red, G3 yellow, G5 purple) consistent across all outputs (PNG, PDF, KMZ)
- CHANGELOG + updated README with CLI reference for all 15 commands
- Interactive dispersion picker screenshots in `docs/`

---

## v1.0.0 — 2026-10-17

Initial release — core pipeline (ERT, MASW, correlations, fence, PDF).
