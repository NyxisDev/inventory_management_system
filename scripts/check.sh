#!/usr/bin/env bash
# Project checks. Run from anywhere: bash scripts/check.sh [--fix] [--security]
#   --fix       apply safe auto-fixes and format the code first
#   --security  also run pip-audit and npm audit (needs network)
# Parts of the project that do not exist yet are skipped.
set -u
cd "$(dirname "$0")/.."

fix=0
security=0
for arg in "$@"; do
  case "$arg" in
    --fix) fix=1 ;;
    --security) security=1 ;;
    *) echo "Unknown option: $arg"; exit 2 ;;
  esac
done

failed=0
step() { echo; echo "==> $*"; }

# ---------- backend: ruff + ty ----------
if [ -f backend/pyproject.toml ]; then
  if command -v ruff >/dev/null 2>&1 && command -v ty >/dev/null 2>&1; then
    (
      cd backend || exit 1
      status=0
      if [ "$fix" = 1 ]; then
        step "ruff check --fix"; ruff check --fix . || status=1
        step "ruff format"; ruff format . || status=1
      else
        step "ruff check"; ruff check . || status=1
        step "ruff format --check"; ruff format --check . || status=1
      fi
      step "ty check"
      if [ -d .venv ]; then ty check --python .venv || status=1; else ty check || status=1; fi
      if [ "$security" = 1 ]; then
        step "pip-audit"
        if command -v pip-audit >/dev/null 2>&1 && [ -f requirements.txt ]; then
          pip-audit -r requirements.txt || status=1
        else
          echo "skipped (pip-audit or requirements.txt missing)"
        fi
      fi
      exit "$status"
    ) || failed=1
  else
    echo "ruff or ty not found. Install: pip install -r backend/requirements-dev.txt"
    failed=1
  fi
else
  echo "backend/: not created yet, skipped"
fi

# ---------- frontends: the lint script created by Quasar ----------
for app in admin-app shop-site; do
  if [ -f "$app/package.json" ]; then
    if [ -d "$app/node_modules" ]; then
      step "$app: npm run lint"
      (cd "$app" && npm run lint --silent) || failed=1
      if [ "$security" = 1 ]; then
        step "$app: npm audit"
        (cd "$app" && npm audit --audit-level=high) || failed=1
      fi
    else
      echo "$app/: dependencies not installed (npm ci), skipped"
    fi
  else
    echo "$app/: not created yet, skipped"
  fi
done

echo
if [ "$failed" = 0 ]; then echo "All checks passed."; else echo "Checks FAILED."; fi
exit "$failed"
