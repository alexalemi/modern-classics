import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import prep as P
import refs as R

inv = R.inventory()
for t in ["see the notes to III. xxiv. and xxxii.",
          "Concerning envy see the notes to III. xxiv. and xxxii.  These"]:
    print(repr(t))
    for m in P.BARE.finditer(t):
        print("   span:", repr(m.group(0)))
    print("   ->", repr(P.resolve_bare(3, t, inv)))
    print()
