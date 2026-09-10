#!/usr/bin/env python3
"""Demonstrate a T-L9b mutant that the frozen gate does not reject.

The mutant checks the trajectory bound only on the nonlinear b/d blocks, even
though contract v3.9 requires ||z|| <= 100 for every latent component.
It operates on a temporary copy and never edits the frozen tree.
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
GATE = HERE.parent / "executable-proofs" / "gate"

with tempfile.TemporaryDirectory(prefix="round6-mutant-") as td:
    dst = pathlib.Path(td) / "gate"
    shutil.copytree(GATE, dst, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    p = dst / "reference_generator.py"
    src = p.read_text()
    old = 'max_abs = float(np.max(np.abs(Z)))'
    new = 'max_abs = float(np.max(np.abs(Z[..., :self.sl["d"].stop])))  # MUTANT: ignores w/x blocks'
    assert old in src
    p.write_text(src.replace(old, new, 1))
    proc = subprocess.run([sys.executable, "run_gate.py"], cwd=dst)
    print(f"MUTANT_GATE_EXIT={proc.returncode}")
    raise SystemExit(proc.returncode)
