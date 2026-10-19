# Changelog

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
