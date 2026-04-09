#!/usr/bin/env bash
# Download the raw evaluation results (47 MB compressed, ~200 MB unpacked)
# from the Zenodo deposit into publication/results/.
#
# These JSONs are the inputs that publication/reports/paper_figures.Rmd reads
# to regenerate every main and Extended Data figure in the paper.
#
# Usage:
#   ./publication/data/download_results.sh
#
# After this runs, you can regenerate all figures with:
#   Rscript -e "rmarkdown::render('publication/reports/paper_figures.Rmd')"
#
# The archive is hosted at:
#   https://doi.org/10.5281/zenodo.19476756
#
# Deposit citation:
#   Bianchi, V. & Schokker, D. Mentori — code, data, and supplementary
#   materials for "Systematic Ablation Reveals Hidden Failures in Multi-Agent
#   AI for Science". Zenodo (2026). https://doi.org/10.5281/zenodo.19476756

set -euo pipefail

# Resolve paths relative to this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
RESULTS_DIR="${REPO_ROOT}/publication/results"
ARCHIVE_URL="https://zenodo.org/records/19476756/files/mentori_results.tar.gz?download=1"
ARCHIVE_PATH="${RESULTS_DIR}/mentori_results.tar.gz"

mkdir -p "${RESULTS_DIR}"

# Skip if already populated (look for any exp JSON file)
if ls "${RESULTS_DIR}"/exp*_*.json >/dev/null 2>&1; then
  echo "[skip] ${RESULTS_DIR} already contains experiment result files."
  echo "       Delete them first if you want to re-download."
  exit 0
fi

echo "[1/3] Downloading mentori_results.tar.gz from Zenodo..."
echo "      ${ARCHIVE_URL}"
if command -v curl >/dev/null 2>&1; then
  curl -L --fail --progress-bar -o "${ARCHIVE_PATH}" "${ARCHIVE_URL}"
elif command -v wget >/dev/null 2>&1; then
  wget -O "${ARCHIVE_PATH}" "${ARCHIVE_URL}"
else
  echo "ERROR: neither curl nor wget is available on this system." >&2
  exit 1
fi

echo "[2/3] Extracting into ${RESULTS_DIR}/..."
tar -xzf "${ARCHIVE_PATH}" -C "${REPO_ROOT}/publication/"
# The tarball is rooted at "results/", so this unpacks into publication/results/

echo "[3/3] Cleaning up archive..."
rm -f "${ARCHIVE_PATH}"

file_count=$(find "${RESULTS_DIR}" -type f -name '*.json' | wc -l | tr -d ' ')
echo ""
echo "Done. ${file_count} experiment result files in ${RESULTS_DIR}/"
echo "Run the following to regenerate all paper figures:"
echo "  Rscript -e \"rmarkdown::render('publication/reports/paper_figures.Rmd')\""
