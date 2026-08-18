"""Re-run prep.py and PROVE that chapters/ did not move.

The bunyan rule: a prep re-run after translation has begun is safe only
if every source file is byte-identical afterwards. A boundary that
shifted by one paragraph would invalidate finished translations and
nothing downstream would notice.
"""
import hashlib
import pathlib
import subprocess
import sys

BOOK = pathlib.Path(__file__).resolve().parent


def digest():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((BOOK / "chapters").glob("*.txt"))}


before = digest()
subprocess.run([sys.executable, str(BOOK / "prep.py")], check=True)
after = digest()

if before != after:
    gone = sorted(set(before) - set(after))
    new = sorted(set(after) - set(before))
    moved = sorted(k for k in before.keys() & after.keys()
                   if before[k] != after[k])
    print(f"CHAPTERS MOVED -- removed {gone}, added {new}, changed {moved}")
    raise SystemExit(1)
print(f"chapters/ unchanged across the re-run ({len(after)} files)")
