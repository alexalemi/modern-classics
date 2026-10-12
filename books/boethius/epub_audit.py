"""Audit the BUILT epub, which nothing else in the toolchain looks at.

`se build-manifest` lists what is on disk rather than what is used,
`se lint` passes, and epubcheck has no opinion about an image nobody
asked for -- so the symbolic-logic bug (248 plates in the package,
referenced by nothing) was invisible to every step. Compare images
referenced against images present, BOTH directions, and count the
verse blocks the page and the epub should agree on.
"""
import pathlib
import re
import sys
import zipfile

epub = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else
                    "site/ebooks/boethius_the-consolation-of-philosophy.epub")
z = zipfile.ZipFile(epub)
names = z.namelist()

present = {n.rsplit("/", 1)[-1] for n in names
           if re.search(r"\.(jpg|jpeg|png|gif|svg)$", n, re.I)}
referenced = set()
verse = chapters = 0
for n in names:
    if not n.endswith(".xhtml"):
        continue
    s = z.read(n).decode()
    referenced |= {m.rsplit("/", 1)[-1]
                   for m in re.findall(r'src="([^"]+)"', s)}
    verse += len(re.findall(r'epub:type="z3998:(?:verse|poem|song)"', s))
    chapters += len(re.findall(r'epub:type="[^"]*chapter', s))

print(f"{epub.name}  {epub.stat().st_size/1e6:.1f} MB, {len(names)} entries")
print(f"images present:    {len(present)}")
print(f"images referenced: {len(referenced)}")
print(f"referenced but MISSING: {sorted(referenced - present) or 'none'}")
print(f"present but UNUSED:     {sorted(present - referenced) or 'none'}")
print(f"verse/song blocks: {verse}")
print(f"chapter-typed files: {chapters}")
