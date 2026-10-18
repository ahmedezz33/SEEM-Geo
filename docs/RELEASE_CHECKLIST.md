# Pre-Release Checklist

Follow this checklist before publishing a new version.

---

## 1. Code & Tests

- [ ] All `__init__.py` and public modules import cleanly:
  `python -c "import seem_geo; print(seem_geo.__version__)"`
- [ ] Full pipeline runs end-to-end on example data:
  `seem-geo pipeline --project examples/example_project.seemproj`
- [ ] CLI help shows all commands:
  `seem-geo --help`
- [ ] GUI launches without errors:
  `seem-geo gui`
- [ ] No `pdb.set_trace()`, `print(…)` debug statements, or TODO stubs left

## 2. Version Bump

- [ ] `seem_geo/__init__.py` → `__version__ = 'X.Y.Z'`
- [ ] `setup.py` → `version='X.Y.Z'`
- [ ] `CITATION.cff` → `version: "X.Y.Z"` + `date-released: "YYYY-MM-DD"`
- [ ] `.zenodo.json` title still accurate
- [ ] `README.md` version badge updated

## 3. Documentation

- [ ] `CHANGELOG.md` has new section with date and all changes
- [ ] `README.md` quick-start commands still work
- [ ] `docs/USER_GUIDE_AR.md` reflects any new CLI commands
- [ ] `docs/PUBLISH_TO_GITHUB.md` links still valid
- [ ] No `ahmedezz33` placeholders left in docs

## 4. Testing on Clean Environment

```bash
python -m venv /tmp/clean_test
source /tmp/clean_test/bin/activate  # Mac/Linux
# or: /tmp/clean_test/Scripts/activate  # Windows
pip install -e .
seem-geo gen-data --out /tmp/test_data
seem-geo init --output /tmp/clean.seemproj
# edit paths...
seem-geo pipeline --project /tmp/clean.seemproj
```

- [ ] All 7 pipeline stages complete without errors
- [ ] PDF report opens cleanly
- [ ] KMZ opens in Google Earth

## 5. Git & GitHub

- [ ] All changes committed:
  `git status` shows clean working tree
- [ ] Pushed to main:
  `git push origin main`
- [ ] CI green on all platforms (check GitHub Actions tab)
- [ ] No open critical bugs tagged for this release

## 6. Release

- [ ] Tag release:
  `git tag -a vX.Y.Z -m "Release X.Y.Z — short description"`
- [ ] Push tag:
  `git push origin vX.Y.Z`
- [ ] CI builds .exe automatically (watch Actions tab)
- [ ] GitHub Release created with changelog + .exe attached
- [ ] (Optional) PyPI release successful:
  `pip install seem-geo==X.Y.Z` works

## 7. Post-Release

- [ ] Zenodo DOI generated (if configured)
- [ ] LinkedIn post with release link
- [ ] Email notification to users/collaborators
- [ ] Documentation site rebuilt (GitHub Pages)
- [ ] Thesis-committee notified if relevant

## 8. Rollback Plan (if something breaks)

If a critical bug is found post-release:

1. **Immediate:** mark the release as pre-release on GitHub to hide from "Latest release"
2. **Investigate:** reproduce the bug and write a failing test
3. **Patch:** release `vX.Y.(Z+1)` with the fix
4. **Communicate:** update CHANGELOG with notes about the bad release
5. **Yank from PyPI** if widely-exploited:
  `pip install twine && twine yank --version X.Y.Z seem-geo`

---

## Version Numbering (SemVer)

- **Major (X)** — breaking changes (API changes, project file schema changes)
- **Minor (Y)** — new features (backwards-compatible)
- **Patch (Z)** — bug fixes only
