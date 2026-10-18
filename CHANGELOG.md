# Changelog

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
