@echo off
REM =============================================================================
REM SEEM Geo — First-time setup script (Windows)
REM =============================================================================
REM Replaces USERNAME with your actual GitHub username, initializes git,
REM and prepares the project for first push.
REM Usage: scripts\first_time_setup.bat <YOUR_GITHUB_USERNAME>
REM =============================================================================

setlocal

if "%~1"=="" (
  echo Usage: %0 ^<YOUR_GITHUB_USERNAME^>
  echo Example: %0 example-user
  exit /b 1
)

set USERNAME=%1
echo ========================================================================
echo  SEEM Geo — First-time Setup
echo ========================================================================
echo.
echo  GitHub username: %USERNAME%
echo.

REM 1. Replace USERNAME in files using PowerShell
echo [1/5] Replacing USERNAME placeholders...
for %%f in (
  "README.md"
  "pyproject.toml"
  "setup.py"
  ".zenodo.json"
  "CITATION.cff"
  "mkdocs.yml"
  "docs\USER_GUIDE_AR.md"
  "docs\PUBLISH_TO_GITHUB.md"
  "docs\index.md"
  "docs\RELEASE_CHECKLIST.md"
  ".github\dependabot.yml"
) do (
  if exist %%f (
  powershell -Command "(Get-Content %%f) -replace 'USERNAME', '%USERNAME%' | Set-Content %%f"
  echo  * %%f
  )
)

REM 2. Initialize git
echo.
echo [2/5] Initializing git...
if not exist .git (
  git init
  git branch -M main
  echo  * Initialized
) else (
  echo  * Already initialized
)

REM 3. Stage files
echo.
echo [3/5] Staging files...
git add .

REM 4. First commit
echo.
echo [4/5] Creating initial commit...
git commit -m "feat: initial release - SEEM Geo v1.1.0"

REM 5. Instructions
echo.
echo [5/5] Next steps:
echo.
echo  1. Create a new repo at: https://github.com/new
echo  Name: seem-geo
echo  DO NOT initialize with README
echo.
echo  2. Link and push:
echo  git remote add origin https://github.com/%USERNAME%/seem-geo.git
echo  git push -u origin main
echo.
echo  3. Create first release:
echo  git tag -a v1.1.0 -m "SEEM Geo v1.1.0"
echo  git push origin v1.1.0
echo.
echo ========================================================================
echo  Local setup complete. Ready to push to GitHub.
echo ========================================================================
endlocal
