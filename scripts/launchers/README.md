# SEEM Geo — Double-Click Launchers

Three Windows `.bat` files for launching SEEM Geo without typing commands.

## Files

| File | Opens | Shortcut |
|------|-------|----------|
| `SEEM_Geo_Pro.bat`      | Pro GUI (6-tab settings, 3-column dashboard, viewer) | Double-click |
| `SEEM_Geo_Standard.bat` | Classic GUI                                           | Double-click |
| `SEEM_Geo_Settings.bat` | Settings dialog only (DPI, inversion, filters, QC)   | Double-click |

## How to install (one-time)

### Option 1 — Keep them in the SEEM Geo folder

If you cloned or downloaded this repo:

```powershell
# Already there in scripts\launchers\ — just double-click.
```

### Option 2 — Put them on the Desktop

```powershell
$desktop = [Environment]::GetFolderPath('Desktop')
copy scripts\launchers\SEEM_Geo_Pro.bat      "$desktop\"
copy scripts\launchers\SEEM_Geo_Standard.bat "$desktop\"
copy scripts\launchers\SEEM_Geo_Settings.bat "$desktop\"
```

### Option 3 — Pin to Start menu

Right-click each `.bat` → "Pin to Start".

### Option 4 — Create a true Windows shortcut (.lnk) with a custom icon

```powershell
$WshShell = New-Object -ComObject WScript.Shell
$shortcut = $WshShell.CreateShortcut("$([Environment]::GetFolderPath('Desktop'))\SEEM Geo Pro.lnk")
$shortcut.TargetPath = (Resolve-Path .\SEEM_Geo_Pro.bat).Path
$shortcut.IconLocation = "$env:SystemRoot\System32\SHELL32.dll,13"   # change index for a different icon
$shortcut.WorkingDirectory = (Resolve-Path .).Path
$shortcut.Save()
```

## Troubleshooting

- **"python is not recognized"** — Python isn't on PATH. Reinstall Python with "Add to PATH" ticked, or edit the `.bat` to use the full python path, e.g. `C:\Users\<you>\AppData\Local\Python\pythoncore-3.15-64\python.exe`.
- **Window flashes and closes** — The launcher's `pause` only fires on error. If the GUI opens then crashes silently, run the command manually from PowerShell to see the error.
- **ModuleNotFoundError: No module named 'seem_geo'** — Install the package first:
  ```powershell
  pip install --upgrade --force-reinstall --no-deps "https://github.com/ahmedezz33/SEEM-Geo/archive/refs/heads/main.zip"
  ```
