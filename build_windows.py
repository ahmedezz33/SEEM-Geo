"""
Windows .exe builder — uses PyInstaller to bundle SEEM Geo into a standalone
executable that includes Python + all dependencies.

Usage (on Windows, in your Anaconda/venv):
  pip install pyinstaller
  python build_windows.py

Produces:
  dist/SEEM_Geo.exe  — standalone single-file executable (~150 MB)
  dist/SEEM_Geo/  — folder-based build (faster startup)
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path


HERE = Path(__file__).parent.resolve()
APP_NAME = 'SEEM_Geo'
MAIN_SCRIPT = HERE / 'seem_geo' / 'gui' / 'main_window.py'


def check_pyinstaller():
  try:
  import PyInstaller
  print(f'  ✓ PyInstaller v{PyInstaller.__version__}')
  return True
  except ImportError:
  print('  ✗ PyInstaller not installed. Run: pip install pyinstaller')
  return False


def build_single_file():
  """One self-contained .exe (larger, slower to start, but easy to share)."""
  print('\n[1/2] Building single-file executable...')
  cmd = [
  sys.executable, '-m', 'PyInstaller',
  '--name', APP_NAME,
  '--onefile',
  '--windowed',
  '--clean',
  '--noconfirm',
  '--add-data', f'{HERE / "examples"}{os.pathsep}examples',
  '--hidden-import', 'tkinter',
  '--hidden-import', 'matplotlib.backends.backend_tkagg',
  '--hidden-import', 'matplotlib.backends.backend_pdf',
  '--hidden-import', 'scipy.sparse.linalg',
  '--hidden-import', 'seem_geo.core.ert',
  '--hidden-import', 'seem_geo.core.masw',
  '--hidden-import', 'seem_geo.core.correlations',
  '--hidden-import', 'seem_geo.core.fence',
  '--hidden-import', 'seem_geo.core.project',
  '--hidden-import', 'seem_geo.reports.pdf_report',
  '--hidden-import', 'seem_geo.reports.vs30_map',
  '--hidden-import', 'seem_geo.io.importers',
  '--hidden-import', 'seem_geo.io.kmz_exporter',
  str(MAIN_SCRIPT),
  ]
  result = subprocess.run(cmd, cwd=HERE)
  if result.returncode == 0:
  print(f'  ✓ Built: dist/{APP_NAME}.exe')


def build_folder():
  """Folder-based build (faster startup, split files)."""
  print('\n[2/2] Building folder distribution...')
  cmd = [
  sys.executable, '-m', 'PyInstaller',
  '--name', APP_NAME,
  '--windowed',
  '--clean',
  '--noconfirm',
  '--add-data', f'{HERE / "examples"}{os.pathsep}examples',
  '--hidden-import', 'tkinter',
  '--hidden-import', 'matplotlib.backends.backend_tkagg',
  '--hidden-import', 'matplotlib.backends.backend_pdf',
  '--hidden-import', 'scipy.sparse.linalg',
  '--hidden-import', 'seem_geo.core.ert',
  '--hidden-import', 'seem_geo.core.masw',
  '--hidden-import', 'seem_geo.core.correlations',
  '--hidden-import', 'seem_geo.core.fence',
  '--hidden-import', 'seem_geo.core.project',
  '--hidden-import', 'seem_geo.reports.pdf_report',
  '--hidden-import', 'seem_geo.reports.vs30_map',
  '--hidden-import', 'seem_geo.io.importers',
  '--hidden-import', 'seem_geo.io.kmz_exporter',
  str(MAIN_SCRIPT),
  ]
  result = subprocess.run(cmd, cwd=HERE)
  if result.returncode == 0:
  print(f'  ✓ Built: dist/{APP_NAME}/')
  # Create a shortcut inside the dist
  shortcut = Path('dist') / APP_NAME / 'Run SEEM Geo.bat'
  shortcut.write_text(f'@echo off\nstart "" "%~dp0{APP_NAME}.exe"\n')


def main():
  print(f'SEEM Geo Windows Builder')
  print(f'{"=" * 50}')
  if not check_pyinstaller(): return 1
  print(f'\n  Source: {MAIN_SCRIPT}')
  print(f'  Output: {HERE / "dist"}')
  print(f'  Platform: {sys.platform}  ·  Python {sys.version.split()[0]}')

  # Clean previous builds
  for d in ['build', 'dist', f'{APP_NAME}.spec']:
  p = HERE / d
  if p.exists():
  if p.is_dir(): shutil.rmtree(p, ignore_errors=True)
  else: p.unlink()

  build_single_file()
  build_folder()

  print(f'\n{"=" * 50}')
  print(f'✅ Build complete.')
  print(f'  To ship: zip the dist/{APP_NAME}/ folder and send.')
  print(f'  Users don\'t need Python installed to run the .exe.')
  return 0


if __name__ == '__main__':
  sys.exit(main())
