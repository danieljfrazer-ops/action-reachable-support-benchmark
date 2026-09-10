"""Gate runner. The criterion is the EXIT CODE. Usage: python3 run_gate.py
Checks interpreter and dependencies first (CX-02/GM-9), runs tests, then the mutation run."""
import importlib, sys, traceback, pathlib, platform, subprocess
here = pathlib.Path(__file__).parent; sys.path.insert(0, str(here))
print(f"interpreter: {sys.executable}  python {platform.python_version()}")
try:
    import numpy; print(f"numpy {numpy.__version__}")
    pins = dict(l.strip().split("==") for l in (here / "requirements.txt").read_text().split() if "==" in l)
    if numpy.__version__ != pins.get("numpy", numpy.__version__) or not platform.python_version().startswith("3.12."):
        print(f"ERROR: environment does not match pins (need python 3.12.x, numpy=={pins.get('numpy')}); create the documented venv"); sys.exit(2)
except ImportError:
    print("ERROR: numpy not importable in this interpreter. Create the documented environment:\n"
          "  python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt\n"
          "then run: python run_gate.py"); sys.exit(2)
failed = passed = 0
for mod in ("test_gate", "test_generator", "test_proof_theatre"):
    m = importlib.import_module(mod)
    for name in sorted(n for n in dir(m) if n.startswith("test_")):
        try: getattr(m, name)(); passed += 1; print(f"PASS {mod}.{name}")
        except Exception: failed += 1; print(f"FAIL {mod}.{name}"); traceback.print_exc()
print(f"\ntests: {passed} passed, {failed} failed"); sys.stdout.flush()
if failed: sys.exit(1)
r = subprocess.run([sys.executable, str(here / "mutants.py")]); sys.stdout.flush()
print(f"GATE {'PASS' if r.returncode == 0 else 'FAIL'}: tests {passed}/{passed+failed}, mutation exit {r.returncode}"); sys.exit(r.returncode)
