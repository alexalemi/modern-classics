"""Representative cases for the reference resolver, one per shape class
that gave trouble. Run it after any change to refs.parse.

Several of these are here because they once resolved to something that
LOOKED right: "(by Prop. xvi., Part i.)" put its Part marker after the
item and quietly resolved to the Part the citation sits in.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import refs as R

CASES = [
    # (inner text, Part it occurs in, expected rendering or None to
    #  assert only that it parses and validates)
    ("what is the same thing, by Prop. xvi., Part i.", 2,
     "Part 1, Proposition 16"),
    ("the same Def. vii. Part I.", 3, "Part 1, Definition 7"),
    ("by Prop. xxviii. of Part i.", 2, "Part 1, Proposition 28"),
    ("Part i., Prop. xv.", 2, "Part 1, Proposition 15"),
    ("Pt. i., Prop. xxxii., Corolls. i. and ii.", 2, None),
    ("II. viii. Coroll.", 1, "Part 2, Proposition 8, Corollary"),
    ("I. xvii. Coroll. ii.", 2, "Part 1, Proposition 17, Corollary 2"),
    ("by Prop. iv.", 1, "Proposition 4 of this Part"),
    ("Def. of the Emotions, xiii.", 4, "Definition 13 of the Emotions"),
    ("III. Deff. i. and ii.", 4, None),
    ("I. Ax. vi", 2, "Part 1, Axiom 6"),
    ("Corollary, Prop vi.", 1, "Proposition 6 of this Part, Corollary"),
    ("in the note to Prop. x.", 1, "Proposition 10 of this Part, Note"),
    ("IV. Ax.", 4, "the Axiom of this Part"),
    ("as we showed in Pt. II.", 4, "Part 2"),
    ("Lemma iii.", 2, "Lemma 3 of this Part"),
    # "and" detaches the numeral from the open qualifier: this is
    # Proposition 6's Corollary AND Proposition 7, not "Corollary 7".
    ("II. vi. Coroll. and vii.", 2,
     "Proposition 6 of this Part, Corollary; Proposition 7 of this Part"),
]


def main():
    inv = R.inventory()
    bad = 0
    for inner, here, want in CASES:
        parsed, ok = R.parse(R.LEAD.sub("", inner), here)
        got = "; ".join(r.render(here) for r in parsed)
        valid = ok and all(r.valid(inv, here) for r in parsed)
        good = valid and (want is None or got == want)
        bad += not good
        print(f"{'ok ' if good else '!! '}P{here}: {inner[:42]:<44} -> {got}")
    print(f"\n{len(CASES)} cases, {bad} failing")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
