#!/usr/bin/env python3
"""Content repairs from the 2026-10-09 audit (ROADMAP.md, "Audit of the
22 MODEL=unknown books"). Idempotent: each edit checks for its own
result before applying, and refuses loudly if neither the old nor the
new text is found.

1. 033: an invented bracketed commentary on Tocqueville's framing of
   slavery -- no source behind it. Deleted.
2. The 1899 editor's bracketed notes ([[...]] in chapters/) had been
   absorbed into Tocqueville's own voice in 012, 021, 032 and 104 (and
   017's 1861 "Trans. Note" on the party names). Each is now its own
   paragraph in the form 035/037/038 already use: "[An editorial note
   from the original translation: ...]", content kept.
3. Tocqueville in the third person inside his own text (002, 003, 008,
   013, 017, 083, and 029's unbracketed rendering of his own footnote): returned to the
   first person or to the source's own construction.
4. 021: "invaded by a foreign power" -> Tocqueville's "barbarians".
5. Fifteen leftover splitter heading lines ("Chapter XVIII: ... — Part
   V") at the top of continuation files; assemble set them as <h4>s
   in the middle of stitched chapters. Removed (and 003's "***" with
   it -- the source has no break at that seam).
6. 038: the dropped "As often as a steady resistance is offered to the
   Federal Government it will be found to yield." restored.
"""
import pathlib
import re

MOD = pathlib.Path(__file__).resolve().parent / "modern_chapters"
NOTE = "[An editorial note from the original translation: {}]"

EDITS = {
    "033.txt": [
        ("\n\n[The passage above reflects Tocqueville's 1830s perspective "
         "on the psychological devastation of slavery. His observations "
         "about what oppression does to people are incisive, but his "
         "framing sometimes conflates the damage done by the system with "
         "the nature of those trapped within it.]", ""),
    ],
    "012.txt": [
        (" The period during which President Buchanan remained in office "
         "after Abraham Lincoln's election — from November 1860 to March "
         "1861 — was the very interval that allowed the seceding Southern "
         "states to complete their preparations for the Civil War, while "
         "the federal government stood paralyzed. No greater disaster "
         "could befall a nation.",
         "\n\n" + NOTE.format(
             "This, however, may be a great danger. The period during "
             "which President Buchanan remained in office after Abraham "
             "Lincoln's election — from November 1860 to March 1861 — was "
             "the very interval that allowed the seceding Southern states "
             "to complete their preparations for the Civil War, while the "
             "federal government stood paralyzed. No greater disaster "
             "could befall a nation.")),
        ("It's worth noting that the calm doesn't always return so "
         "smoothly. The election of Abraham Lincoln was the signal for "
         "civil war.",
         NOTE.format("Not always. The election of Abraham Lincoln was the "
                     "signal for civil war.")),
    ],
    "021.txt": [
        (" Events since Tocqueville's time have confirmed exactly this "
         "prediction.",
         "\n\n" + NOTE.format("That is precisely what has since "
                              "occurred.")),
        ("invaded by a foreign power", "invaded by barbarians"),
    ],
    "032.txt": [
        ("The Anglo-American democracy, until the Civil War, was the only "
         "one that managed to maintain itself in peace.",
         "The Anglo-American democracy is the only one that has so far "
         "managed to maintain itself in peace.\n\n" + NOTE.format(
             "A remark that, since the great Civil War of 1861–65, no "
             "longer applies.")),
        (" A prediction that Tocqueville wrote in 1832, which was realized "
         "to the letter when Napoleon III seized power in France in 1852.",
         "\n\n" + NOTE.format(
             "This prediction of France's return to imperial despotism, "
             "and of the true character of that despotic power, was "
             "written in 1832 and realized to the letter in 1852, when "
             "Napoleon III seized power.")),
    ],
    "104.txt": [
        ("(It's worth noting that later experience has shown job-hunting "
         "to be just as intense",
         "[An editorial note from the original translation: Later "
         "experience has in fact shown job-hunting to be just as intense"),
        ("titles of rank are in aristocratic countries.)",
         "titles of rank are in aristocratic countries.]"),
    ],
    "017.txt": [
        (" (It's worth noting that the meaning of these party names "
         "eventually reversed: the Republicans of Tocqueville's era became "
         "the forerunners of the modern Democratic Party, while the "
         "principles of the old Federalists eventually found a home in the "
         "modern Republican Party.)", ""),
        ("Many years have now passed since the Federalists ceased to exist "
         "as a party.",
         "Many years have now passed since the Federalists ceased to exist "
         "as a party.\n\n" + NOTE.format(
             "It hardly needs saying that the meaning of these party "
             "names has since changed: the Republicans now represent the "
             "old Federalists, and the Democrats the old Republicans. "
             "(1861)")),
    ],
    "002.txt": [
        ("Tocqueville himself noted that he had seen fragments of it "
         "carefully preserved in several American towns — a testament, he "
         "thought, to how all human power and greatness ultimately resides "
         "in the human soul.",
         "It has become an object of veneration in the United States: I "
         "have seen fragments of it carefully preserved in several American "
         "towns. Doesn't that show how entirely all human power and "
         "greatness resides in the human soul?"),
    ],
    "003.txt": [
        ("was still ahead of what most nations had achieved even in "
         "Tocqueville's own time.",
         "is still ahead of the freedoms of our own age."),
    ],
    "008.txt": [
        ("(Tocqueville pointed to China as the most complete example of "
         "what thoroughgoing centralized administration produces: peace "
         "without happiness,",
         "(China seems to me the most complete example of what "
         "thoroughgoing centralized administration produces: travelers "
         "tell us the Chinese have peace without happiness,"),
        ("The condition of society is always tolerable, never excellent.)",
         "The condition of society there is always tolerable, never "
         "excellent.)"),
    ],
    "013.txt": [
        ("(By Tocqueville's time, there were twenty-four.)",
         "That number has now grown to twenty-four."),
    ],
    # 083: the whole paragraph was narrated from a later vantage
    # ("had been", "at that time"); the source is present tense, and
    # "[in 1840]" is the 1899 editor's gloss, not Tocqueville's.
    "083.txt": [
        ("The United States had been independent for barely half a "
         "century when Tocqueville was writing, and had only recently "
         "emerged from colonial dependence on Great Britain. The number of "
         "great fortunes was still small, and capital was scarce. Yet no "
         "country in the world had made faster progress in trade and "
         "manufacturing. The Americans were already the second-greatest "
         "maritime power on earth, and although their manufacturers faced "
         "nearly impossible natural obstacles, they were making rapid "
         "advances every day.",
         "The United States has been free of its colonial dependence on "
         "Great Britain for barely half a century. The number of great "
         "fortunes there is still small, and capital is scarce. Yet no "
         "country in the world has made faster progress in trade and "
         "manufacturing. The Americans are already the second-greatest "
         "maritime power on earth, and although their manufacturers face "
         "nearly impossible natural obstacles, they are making rapid "
         "advances every day."),
        ("The Americans had arrived on their territory only yesterday, yet "
         "they had already remade the natural order to serve their "
         "advantage. They had connected the Hudson River to the Mississippi "
         "and linked the Atlantic Ocean to the Gulf of Mexico, spanning a "
         "continent of more than five hundred leagues. The longest railroads "
         "in the world at that time were in America.",
         "The Americans arrived on their territory only yesterday, yet they "
         "have already remade the natural order to serve their advantage. "
         "They have connected the Hudson River to the Mississippi and linked "
         "the Atlantic Ocean to the Gulf of Mexico, spanning a continent of "
         "more than five hundred leagues. The longest railroads built "
         "anywhere so far are in America."),
    ],
    # 029: Tocqueville's own footnote on the great cities, narrated about
    # him ("Tocqueville added a revealing note... he observed"), and its
    # closing prediction (that the republics will perish of it unless an
    # armed force independent of the cities is created) had been dropped.
    "029.txt": [
        ("Tocqueville added a revealing note on this point: the United "
         "States had no true capital city, but it already had several large "
         "ones. Philadelphia had 161,000 residents and New York 202,000 in "
         "1830. The lower-income populations of these cities, he observed, "
         "were already more volatile than the urban poor of European "
         "cities. They included free Black Americans, who were condemned by "
         "both law and public opinion to a permanent state of poverty and "
         "degradation, as well as masses of Europeans driven to American "
         "shores by misfortune or misconduct, who brought all the vices of "
         "the Old World without the stabilizing interests that might "
         "counteract them. Having no civil rights, these people were ready "
         "to exploit any social unrest for their own advantage. Serious "
         "riots had recently broken out in both Philadelphia and New York. "
         "Still, these disturbances had no effect on the rest of the "
         "country, because city populations had so far exercised neither "
         "power nor influence over the rural majority. Nevertheless, "
         "Tocqueville considered the size of certain American cities — and "
         "especially the character of their populations — a real danger to "
         "the future of American democracy.",
         "The United States has no true capital city, but it already has "
         "several very large ones: Philadelphia had 161,000 residents and "
         "New York 202,000 in 1830. The lower classes of these cities are "
         "even more volatile than the urban poor of Europe. They include "
         "free Black Americans, condemned by both law and public opinion to "
         "a hereditary state of poverty and degradation, as well as masses "
         "of Europeans driven to American shores by misfortune or "
         "misconduct, who bring all our vices with them and none of the "
         "interests that might counteract them. Having no civil rights, "
         "these people are ready to exploit any social unrest for their own "
         "advantage — and in the last few months serious riots have broken "
         "out in both Philadelphia and New York. Such disturbances are "
         "unknown in the rest of the country, which isn't alarmed by them, "
         "because city populations have so far exercised neither power nor "
         "influence over the rural districts. Nevertheless, I consider the "
         "size of certain American cities — and especially the character "
         "of their populations — a real danger to the future of the "
         "democratic republics of the New World. I'll venture to predict "
         "that they will perish of it, unless their governments manage to "
         "create an armed force that remains under the control of the "
         "national majority while standing independent of the city "
         "populations, and able to put down their excesses."),
    ],
    "038.txt": [
        ("Such a clash is unlikely to be seriously attempted. Experience",
         "Such a clash is unlikely to be seriously attempted. Whenever the "
         "federal government meets steady resistance, it gives way. "
         "Experience"),
    ],
}

# the splitter's own label, left at the top of a continuation file
SPLIT_HEAD = re.compile(r"^Chapter [IVXLC]+: .* — Part [IVXLC]+\n+(\*\*\*\n+)?",
                        re.M)


def main():
    for name, edits in EDITS.items():
        p = MOD / name
        t = p.read_text()
        for old, new in edits:
            # the result first: several old strings survive inside
            # their own replacement (a sentence moved into a note)
            if new and new in t:
                pass
            elif old in t:
                t = t.replace(old, new, 1)
            elif not new:
                pass
            else:
                raise SystemExit(f"{name}: neither old nor new text found: "
                                 f"{old[:60]!r}")
        p.write_text(t)

    for p in sorted(MOD.glob("[0-9][0-9][0-9].txt")):
        t = p.read_text()
        t2, n = SPLIT_HEAD.subn("", t)
        if n:
            p.write_text(t2)
            print(f"{p.name}: removed {n} split heading")


if __name__ == "__main__":
    main()
