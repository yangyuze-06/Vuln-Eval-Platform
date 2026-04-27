#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

DB_DIR="$PROJECT_ROOT/dataset/codefuse-WebGoat-db"
RULE_FILE="$PROJECT_ROOT/rules/codefuse-query/CWE-079/checker079.gdl"
OUT_DIR="$PROJECT_ROOT/experiments/cwe-079/results/webgoat"

mkdir -p "$OUT_DIR"

echo "[debug] PROJECT_ROOT=$PROJECT_ROOT"
echo "[debug] DB_DIR=$DB_DIR"
echo "[debug] RULE_FILE=$RULE_FILE"
echo "[debug] OUT_DIR=$OUT_DIR"

test -d "$DB_DIR" || { echo "[error] DB not found: $DB_DIR"; exit 1; }
test -f "$RULE_FILE" || { echo "[error] rule file not found: $RULE_FILE"; exit 1; }

echo "[1/1] Running CWE-079 checker on WebGoat..."

sparrow query run \
  -d "$DB_DIR" \
  -gdl "$RULE_FILE" \
  -o "$OUT_DIR"

echo "Done."
echo "Result dir: $OUT_DIR"
