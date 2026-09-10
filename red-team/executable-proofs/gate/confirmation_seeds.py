"""D-11.3 confirmation instance set. Development configuration seeds 0..9 are exhausted (round 5). The confirmation seeds are
derived from a secret file held by Daniel OUTSIDE this folder (never in the freeze manifest); only sha256(secret) is frozen here.
Nobody derives or inspects the seeds until the specs and constants are frozen and the pilot is closed. The seed range is
disjoint from every development seed by construction. Usage (after the freeze): python3 confirmation_seeds.py <secret file>."""
import hashlib, sys, pathlib
COMMITMENT = "89a262a92313233bcb037c1c12fd5b9703917296f36feeac3069a5ead2649d01"   # sha256 of the secret bytes, sealed 7 Sep 2026
N_CONFIRMATION = 20                       # D-10.7 floor when the margin is near delta_AUC; the pilot may use fewer, never more
SEED_LOW, SEED_HIGH = 100000, 999999      # disjoint from development seeds 0..9 and from every sub-seed seed*1000+i, i < 60

def derive(secret: bytes):
    if hashlib.sha256(secret).hexdigest() != COMMITMENT: raise ValueError("secret does not match the frozen commitment")
    seeds = []
    for i in range(N_CONFIRMATION):
        h = hashlib.sha256(secret + b":confirmation:" + str(i).encode()).digest()
        seeds.append(SEED_LOW + int.from_bytes(h[:8], "big") % (SEED_HIGH - SEED_LOW + 1))
    if len(set(seeds)) != len(seeds): raise ValueError("collision in the derived seed set; extend N or re-seal")
    return seeds

if __name__ == "__main__":
    print(derive(pathlib.Path(sys.argv[1]).read_bytes()))
