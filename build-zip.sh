#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="$(basename "$PROJECT_DIR")"
PARENT_DIR="$(dirname "$PROJECT_DIR")"
OUTPUT_ZIP="$PARENT_DIR/$PROJECT_NAME.zip"

cd "$PARENT_DIR"
rm -f "$OUTPUT_ZIP"

# Keep the project root folder inside the archive.
zip -r "$OUTPUT_ZIP" "$PROJECT_NAME" \
  -x "*/.git/*" \
     "*/.gitignore" \
     "*/__pycache__/*" \
     "*.pyc" \
     "*.pyo" \
     "*/.DS_Store"

echo "Created: $OUTPUT_ZIP"