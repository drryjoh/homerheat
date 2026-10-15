"""Rebuild every report figure into figures/out/ (each script also runs on its own).

Reads only analysis/results/ and physics/; no model is refit. Takes ~20 s.
Run from the repo root:  .venv/bin/python figures/make_all.py
"""
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

for script in sorted(HERE.glob("fig[0-9][0-9]_*.py")):
    print(f"-> {script.name}")
    runpy.run_path(str(script), run_name="__main__")
