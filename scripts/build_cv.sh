#!/bin/bash
# Regenerate _data/cv.json and files/cv.pdf from _data/Ryan_Alizadeh_CV.yaml.
# Run this after editing the YAML. Requires: pip install -r requirements.txt

set -euo pipefail
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
YAML="$BASE_DIR/_data/Ryan_Alizadeh_CV.yaml"
CV_JSON="$BASE_DIR/_data/cv.json"
RENDER_OUTPUT_DIR="$BASE_DIR/_data/rendercv_output"
PDF_DEST="$BASE_DIR/files/cv.pdf"

echo "==> Generating _data/cv.json from Ryan_Alizadeh_CV.yaml"
python3 "$BASE_DIR/scripts/generate_cv_json.py" --input "$YAML" --output "$CV_JSON"

echo "==> Rendering CV with rendercv"
command -v rendercv >/dev/null 2>&1 || {
  echo "ERROR: 'rendercv' not found. Install it first: pip install -r requirements.txt" >&2
  exit 1
}
( cd "$BASE_DIR/_data" && rendercv render "$(basename "$YAML")" )

GENERATED_PDF="$RENDER_OUTPUT_DIR/Ryan_Alizadeh_CV.pdf"
if [ ! -f "$GENERATED_PDF" ]; then
  echo "ERROR: expected rendercv output not found at $GENERATED_PDF" >&2
  exit 1
fi
cp "$GENERATED_PDF" "$PDF_DEST"
echo "==> Copied PDF to files/cv.pdf"
echo "Done. Run 'bundle exec jekyll serve' and check /cv/."
