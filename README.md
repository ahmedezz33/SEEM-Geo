<div align="center">

<img src="docs/assets/logo.png" alt="SEEM Geo logo" width="150"/>

# SEEM Geo

### Professional ERT & MASW Processing Suite

**For engineering geology · foundation design · site classification**

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23455148.svg)](https://doi.org/10.5281/zenodo.23455148)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.3.2-brightgreen.svg)](CHANGELOG.md)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20Mac-lightgrey.svg)](#installation)
[![CI](https://github.com/ahmedezz33/seem-geo/actions/workflows/ci.yml/badge.svg)](https://github.com/ahmedezz33/seem-geo/actions)
[![Docs](https://img.shields.io/badge/docs-mkdocs-526CFE.svg)](https://ahmedezz33.github.io/seem-geo/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23455148.svg)](https://doi.org/10.5281/zenodo.23455148)
[![Code of Conduct](https://img.shields.io/badge/contributor%20covenant-2.1-5e9bba.svg)](CODE_OF_CONDUCT.md)

[🚀 Quick Start](#-quick-start--30-seconds) ·
[📖 Docs](https://ahmedezz33.github.io/seem-geo/) ·
[🐛 Issues](https://github.com/ahmedezz33/seem-geo/issues) ·
[💬 Discussions](https://github.com/ahmedezz33/seem-geo/discussions)

</div>

---

Built for the HVDC corridor investigation (the author's institution Master's). Processes raw field data → inverted sections → correlation framework → Google Earth KMZ → thesis-ready PDF annex. Includes a desktop GUI, interactive dispersion picker, and Windows standalone .exe builder.

![Workflow](docs/workflow_diagram.png)

---

## ✨ Features

- 🔬 **ERT** (Wenner-alpha) — pseudosection + Occam 2D inversion
- 🌊 **MASW** — f-v image + dispersion pick + Vs(z) + Vs30 + local-code Site Class
- 🎯 **Interactive Dispersion Picker** — click-to-pick with live Vs(z) preview
- 📈 **8-correlation framework** with explicit statistical qualifications (df, R², p, CI)
- 🗺️ **Fence diagrams** — multi-site corridor visualization + resistivity ribbon
- 🌍 **Google Earth KMZ** — 36-placemark export with interactive popups
- 📊 **Vs30 interpolated map** — colour-coded by local-code Site Class
- 📄 **Thesis-ready PDF report** — 58-page annex for Chapter V
- 📂 **Industry importers** — Res2DInv, AGI SuperSting, SurfSeis, SEG-2, SEG-Y
- 💿 **Windows .exe builder** — standalone distribution via PyInstaller
- 🖥️ **Desktop GUI** (Tkinter) + unified CLI
- 🧪 **Realistic field data generator** — synthetic test data matching true geology

---

## 🚀 Installation

### From PyPI (recommended, once published)
```bash
pip install seem-geo
```

### From source
```bash
git clone https://github.com/ahmedezz33/seem-geo.git
cd seem-geo
pip install -e .
```

### Standalone executables (no Python needed)
Download the latest `.exe` / `.app` / Linux binary from the [Releases page](https://github.com/ahmedezz33/seem-geo/releases).

**Requires:** Python ≥ 3.8, numpy, pandas, scipy, matplotlib.

---

## 🎬 Quick Start — 30 seconds

```bash
# 1. Generate realistic test data
seem-geo gen-data --out field_data/

# 2. Create a project
seem-geo init --output my_project.seemproj
# Edit my_project.seemproj to point paths at field_data/

# 3. Run the full pipeline
seem-geo pipeline --project my_project.seemproj
```

That builds **everything** — ERT inversions, MASW Vs(z), correlations, fence diagrams, Vs30 map, KMZ, and 58-page PDF report.

---

## 🖱️ Or launch the GUI

```bash
seem-geo gui
```

A desktop app opens with 4 tabs: **Project**, **Sites**, **Processing**, **Log**. One click runs the whole pipeline.

---

## 📚 Documentation

- 📖 **[User Guide (Arabic)](docs/USER_GUIDE_AR.md)** — 15-section step-by-step walkthrough
- 📘 **[Publishing to GitHub](docs/PUBLISH_TO_GITHUB.md)**
- 📋 **[Release Checklist](docs/RELEASE_CHECKLIST.md)**
- 📝 **[Changelog](CHANGELOG.md)**
- 🤝 **[Contributing](CONTRIBUTING.md)** · [Code of Conduct](CODE_OF_CONDUCT.md) · [Security](SECURITY.md)

Full documentation at **[https://ahmedezz33.github.io/seem-geo/](https://ahmedezz33.github.io/seem-geo/)**

---

## 🗂️ CLI Reference

```bash
seem-geo gui  # Desktop GUI
seem-geo init --output project.seemproj  # New project
seem-geo info --project project.seemproj  # Project summary
seem-geo gen-data --out field_data/  # Realistic test data
seem-geo import --kind ert --input X --output Y # Res2DInv/SurfSeis import
seem-geo ert --project project.seemproj -v  # ERT only
seem-geo masw --project project.seemproj -v  # MASW only
seem-geo corr --project project.seemproj  # Correlations
seem-geo fence --project project.seemproj  # Fence diagrams
seem-geo vs30-map --project project.seemproj  # Vs30 map + chart
seem-geo kmz --project project.seemproj  # Google Earth KMZ
seem-geo report --project project.seemproj  # PDF annex
seem-geo pipeline --project project.seemproj  # Everything in order
seem-geo picker --shot shot.csv  # Interactive dispersion picker
seem-geo build-exe  # Windows standalone .exe
```

---

## 🎨 Group Colours Convention

| Group | Colour | Lithology | Count |
|-------|--------|-----------|-------|
| G1 | 🟢 `#2ECC40` | Schist (metamorphic) | 26 (65.0 %) |
| G2 | 🔴 `#FF4136` | Granite (plutonic) | 3 (7.5 %) |
| G3 | 🟡 `#FFDC00` | Weak sedimentary | 8 (20.0 %) |
| G5 | 🟣 `#B10DC9` | Residual soil / weathered | 3 (7.5 %) |

---

## 🧪 Example — Pipeline test results

Running the full pipeline on 12 synthetic sites produces physically-consistent results:

| Group | Stations | Vs30 (m/s) | Site Class |
|-------|----------|------------|------------|
| G5 Residual | BH3, BH4, BH11 | 282–323 | **D** (stiff soil) |
| G3 Sedimentary | BH1, BH5, BH9 | 291–317 | **D** |
| G1 Schist | BH6, BH7, BH8, BH12 | 602–638 | **C** (very dense) |
| G2 Granite | BH9, BH10 | 648 | **C** |

Correlations with full statistics:
- **ρ vs RQD (G1):** n=4, R²=0.69, status=`min_df`
- **Vs vs N₆₀ (G3+G5):** n=6, R²=0.02, status=`ok`
- **Vs vs RQD (G1):** n=4, R²=0.68, status=`min_df`
- **Vs vs UCS (G1+G3):** n=7, R²=0.93, status=`ok`

---

## 🏗️ Architecture

```
seem_geo/
├── __main__.py  → CLI dispatcher
├── core/
│  ├── project.py  → Project config & I/O
│  ├── ert.py  → Wenner + Occam inversion
│  ├── masw.py  → f-v + Vs(z) + Vs30
│  ├── correlations.py  → 8-correlation framework
│  └── fence.py  → Fence diagrams
├── gui/
│  ├── main_window.py  → Tkinter main app
│  └── dispersion_picker.py → Interactive picker
├── io/
│  ├── importers.py  → Res2DInv/SurfSeis/SEG-2/SEG-Y
│  └── kmz_exporter.py  → Google Earth KMZ
├── reports/
│  ├── pdf_report.py  → 58-page PDF annex
│  └── vs30_map.py  → Vs30 interpolated map
└── data/
  └── realistic_field_generator.py
```

---

## 📣 Citing SEEM Geo

If you use SEEM Geo in your research, please cite it as:

```bibtex
@software{seem_geo_2026,
  author  = {Ahmed},
  title  = {SEEM Geo: Professional ERT \& MASW Processing Suite},
  year  = 2026,
  version  = {1.1.0},
  publisher  = {Zenodo},
  doi  = {10.5281/zenodo.23455148},
  url  = {https://github.com/ahmedezz33/seem-geo}
}
```

See also [`CITATION.cff`](CITATION.cff) for other citation formats.

---

## 📄 License

MIT — see [LICENSE](LICENSE). Free for academic and commercial use.

## 📧 Contact

**Ahmed** · Open-source project
📩 [ahmedezz3@gmail.com](mailto:ahmedezz3@gmail.com)

## 🙏 Acknowledgments

- Thesis supervisor at the author's institution
- Dr. Ahmed Saad for the Chapter I technical review that shaped the correlation framework's statistical qualifications
- Open-source project
- the project operator and the geotechnical contractor for the 40-borehole dataset

---

<div align="center">

**Built for the executed 12 ERT + 12 MASW programme of the linear-infrastructure HVDC corridor**

[⬆ Back to top](#seem-geo)

</div>
