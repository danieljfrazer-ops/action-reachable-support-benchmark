"""L1 demonstration: the old print-only scripts exit 0 even with a wrong formula. This test documents that
and is expected to PASS, proving the old scripts were not a gate. The real gate is test_gate.py."""
import subprocess, sys, pathlib, textwrap
def test_print_only_script_exits_zero_with_wrong_formula():
    wrong = textwrap.dedent("""
        import numpy as np
        A=np.diag([0.9,0.9]); B=np.eye(2)
        M = np.linalg.matrix_power(A, -1) @ B     # acausal, wrong
        print('M =', M)                            # no assert: prints and exits 0
    """)
    p = pathlib.Path(__file__).parent / "_wrong_demo.py"; p.write_text(wrong)
    r = subprocess.run([sys.executable, str(p)], capture_output=True, text=True); p.unlink()
    assert r.returncode == 0   # a demonstration cannot fail; therefore it was never a gate
