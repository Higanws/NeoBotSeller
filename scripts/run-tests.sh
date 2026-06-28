#!/usr/bin/env bash
# Ejecuta tests unitarios de los servicios principales.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FAILED=0

run_suite() {
  local name="$1"
  local dir="$2"
  echo "=== $name ==="
  if (
    cd "$dir"
    if [[ ! -d .venv ]] || [[ ! -x .venv/bin/pytest ]]; then
      python3 -m venv .venv
      . .venv/bin/activate
      pip -q install -r requirements-dev.txt
    else
      . .venv/bin/activate
    fi
    PYTHONPATH=src .venv/bin/pytest tests/ -q
  ); then
    echo "OK: $name"
  else
    echo "FAIL: $name"
    FAILED=1
  fi
  echo
}

run_suite_odoo() {
  echo "=== Odoo/connectors ==="
  if (
    cd "$ROOT/Odoo/connectors"
    if [[ ! -d .venv ]]; then
      python3 -m venv .venv
      . .venv/bin/activate
      pip -q install pytest
    else
      . .venv/bin/activate
    fi
    PYTHONPATH="$ROOT/Odoo" .venv/bin/pytest tests/ -q
  ); then
    echo "OK: Odoo/connectors"
  else
    echo "FAIL: Odoo/connectors"
    FAILED=1
  fi
  echo
}

run_suite "Redis/conversation-service" "$ROOT/Redis/conversation-service"
run_suite "services/ia-core" "$ROOT/services/ia-core"
run_suite "RAG/actions-service" "$ROOT/RAG/actions-service"
run_suite_odoo

if [[ "$FAILED" -ne 0 ]]; then
  exit 1
fi
echo "Todos los tests pasaron."
