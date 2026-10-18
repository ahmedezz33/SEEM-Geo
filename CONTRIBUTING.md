# Contributing to SEEM Geo

Thanks for your interest in contributing! SEEM Geo is a tool built for engineering-geology practitioners working on linear infrastructure projects.

## Ways to contribute

- **Report bugs** — open an issue with the bug-report template
- **Request features** — open an issue with the feature-request template
- **Submit code** — open a pull request against `main`
- **Improve documentation** — PRs to README, USER_GUIDE_AR.md, or docstrings welcome
- **Share example projects** — anonymised `.seemproj` files for other geologies are valuable

## Development setup

```bash
# Clone your fork
git clone https://github.com/YOUR_ahmedezz33/seem-geo.git
cd seem-geo

# Install in editable mode with test extras
pip install -e ".[test]"

# Verify
seem-geo --help
```

## Code style

- **Concise over clever** — if a reviewer has to re-read a line, split it
- **Docstrings** on every public function, class, and module
- **Type hints** where they help (we don't enforce them yet)
- **No breaking changes** without a version bump and CHANGELOG entry

## Testing

Before submitting a PR:

```bash
# 1. Imports work
python -c "import seem_geo; print(f'OK v{seem_geo.__version__}')"

# 2. CLI works
seem-geo --help

# 3. Full pipeline runs
seem-geo gen-data --out /tmp/test_data
seem-geo init --output /tmp/test.seemproj
# edit /tmp/test.seemproj to point paths at /tmp/test_data
seem-geo pipeline --project /tmp/test.seemproj
```

## Adding a new file-format reader

New readers live in `seem_geo/io/importers.py`:

```python
def read_my_format(path):
  """Read .my file format. Returns (DataFrame, metadata_dict)."""
  # Your parsing logic
  df = pd.DataFrame(...)
  return df, {'format_version': ...}
```

Then wire it into `detect_and_read_ert` (or `_masw`) with the file extension.

## Adding a new processing stage

1. Create the processing function in `seem_geo/core/your_module.py`
2. Add a `batch_your_stage(project, progress_callback, verbose)` function
3. Register the stage in `seem_geo/__main__.py` under the dispatch table
4. Add to the pipeline order in `cmd_pipeline`
5. Add CHANGELOG entry

## Commit messages

Please use conventional commits:
- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation only
- `refactor:` code refactoring without behavior change
- `test:` test additions/updates
- `chore:` dependency updates, build system, etc.

Example:
```
feat(masw): add higher-mode dispersion picking

Users can now manually select Rayleigh higher modes in the picker
by holding Shift while clicking. Closes #42.
```

## Questions?

Open a discussion or email your-email@example.com.
