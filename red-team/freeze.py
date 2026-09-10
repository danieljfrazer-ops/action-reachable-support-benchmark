"""Prints the freeze hash: sha256 over the files in freeze-manifest.txt, concatenated in order."""
import hashlib, pathlib
root = pathlib.Path(__file__).parent; h = hashlib.sha256()
for line in (root / "freeze-manifest.txt").read_text().split():
    h.update((root / line).read_bytes())
print(h.hexdigest()[:16])
