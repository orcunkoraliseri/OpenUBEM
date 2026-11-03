#!/bin/bash
#SBATCH --partition=ps
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --job-name=eu22_fix_env
#SBATCH --output=/speed-scratch/o_iseri/eu22_fix_2026-10-10/logs/%x_%j.log

set -euo pipefail

ROOT="${EU22_FIX_ROOT:-/speed-scratch/o_iseri/eu22_fix_2026-10-10}"
ENV_DIR="${EU22_FIX_ENV:-/speed-scratch/o_iseri/envs/openubem_eu22}"
PYBIN="${PYBIN:-python3}"

if [ -e "$ENV_DIR" ]; then
    echo "ERROR: $ENV_DIR already exists; not touching it. Pick another EU22_FIX_ENV or remove it by hand." >&2
    exit 1
fi
[ -f "$ROOT/requirements_eu22.txt" ] || { echo "ERROR: missing $ROOT/requirements_eu22.txt" >&2; exit 1; }

"$PYBIN" -c 'import sys; assert sys.version_info >= (3, 10), sys.version' || {
    echo "ERROR: $PYBIN is older than 3.10 ($("$PYBIN" -V 2>&1)). Re-submit with --export=ALL,PYBIN=<path to python >= 3.10>." >&2
    exit 1
}

mkdir -p "$(dirname "$ENV_DIR")"
"$PYBIN" -m venv "$ENV_DIR"
"$ENV_DIR/bin/python" -m pip install --upgrade pip
"$ENV_DIR/bin/python" -m pip install -r "$ROOT/requirements_eu22.txt"
"$ENV_DIR/bin/python" -c "import shapely, pandas, geopandas; print('ENV_OK', shapely.__version__, pandas.__version__, geopandas.__version__)"
