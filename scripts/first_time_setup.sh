#!/usr/bin/env bash
# =============================================================================
# SEEM Geo — First-time setup script (Linux/Mac)
# =============================================================================
# Replaces USERNAME with your actual GitHub username in all files,
# initializes git, and prepares the project for first push.
# Usage: bash scripts/first_time_setup.sh <YOUR_GITHUB_USERNAME>
# =============================================================================
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <YOUR_GITHUB_USERNAME>"
  echo "Example: $0 example-user"
  exit 1
fi

USERNAME="$1"
echo "========================================================================"
echo "  SEEM Geo — First-time Setup"
echo "========================================================================"
echo ""
echo "  GitHub username: $USERNAME"
echo ""

# 1. Replace all USERNAME placeholders in docs & configs
echo "[1/5] Replacing USERNAME placeholders..."
FILES_TO_UPDATE=(
  "README.md"
  "pyproject.toml"
  "setup.py"
  ".zenodo.json"
  "CITATION.cff"
  "mkdocs.yml"
  "docs/USER_GUIDE_AR.md"
  "docs/PUBLISH_TO_GITHUB.md"
  "docs/index.md"
  "docs/RELEASE_CHECKLIST.md"
  ".github/dependabot.yml"
)

for f in "${FILES_TO_UPDATE[@]}"; do
  if [ -f "$f" ]; then
  sed -i.bak "s/USERNAME/$USERNAME/g" "$f"
  rm -f "${f}.bak"
  echo "  ✓ $f"
  fi
done

# 2. Initialize git
echo ""
echo "[2/5] Initializing git..."
if [ ! -d .git ]; then
  git init
  git branch -M main
  echo "  ✓ Initialized"
else
  echo "  ✓ Already initialized"
fi

# 3. Stage files
echo ""
echo "[3/5] Staging files..."
git add .
echo "  ✓ $(git status --short | wc -l) files staged"

# 4. First commit
echo ""
echo "[4/5] Creating initial commit..."
git commit -m "feat: initial release — SEEM Geo v1.1.0

- ERT processing (Wenner-alpha + Occam inversion)
- MASW processing (f-v + Vs(z) + Vs30 + local-code Site Class)
- 8-correlation framework with statistical qualifications
- Fence diagrams + Vs30 map + Google Earth KMZ
- 58-page thesis-ready PDF report
- Interactive dispersion picker
- Desktop GUI + CLI + Windows .exe builder
- CI/CD, Dependabot, CodeQL, GitHub Pages, Zenodo

Co-authored-by: Dr. Ahmed Saad (Chapter I technical review)" || echo "  (nothing to commit)"

# 5. Instructions for pushing
echo ""
echo "[5/5] Next steps:"
echo ""
echo "  1. Create a new repo at: https://github.com/new"
echo "  Name: seem-geo"
echo "  Visibility: Public (recommended)"
echo "  DO NOT initialize with README (we already have one)"
echo ""
echo "  2. Link and push:"
echo "  git remote add origin https://github.com/$USERNAME/seem-geo.git"
echo "  git push -u origin main"
echo ""
echo "  3. Create first release:"
echo "  git tag -a v1.1.0 -m 'SEEM Geo v1.1.0 — Full-featured'"
echo "  git push origin v1.1.0"
echo ""
echo "  4. Enable GitHub Pages:"
echo "  Settings → Pages → Source: GitHub Actions"
echo ""
echo "========================================================================"
echo "  ✅ Local setup complete. Ready to push to GitHub."
echo "========================================================================"
