#!/usr/bin/env python3
"""Per-book checks for the Discourses that verify.py cannot make.

    python3 epictetus/check.py

verify.py knows completeness, word ratio and part markers. What it
cannot see here:
 1. HEADING DRIFT. All 95 titles were decided in prep.py's TITLES table
    (the quixote rule) and every modern file must open with the exact
    heading its source file opens with. A drifted title is invisible to
    every other check -- the words are all present and the ratio does
    not move -- and it is how a book ends up with five conventions in
    it.
 2. A LINE OF DIALOGUE READ AS A SECTION HEADING. This book is mostly
    dialogue and short lines, which is exactly what assemble.
    is_subheading has misread in six other books. The function itself
    is run here, not an approximation of it.
 3. Markup characters, which this pipeline ships literally.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pathlib, re

import assemble
bad=0; rows=[]
for f in sorted(pathlib.Path('epictetus/modern_chapters').glob('*.txt')):
    n=f.stem
    s=len(open(f'epictetus/chapters/{n}.txt').read().split()); m=len(f.read_text().split())
    r=m/s
    if not 0.85<=r<=1.3: rows.append(f'{n} RATIO {r:.2f} ({s}->{m})'); bad+=1
    lines=[x.strip() for x in f.read_text().split('\n') if x.strip()]
    if lines[0]!=open(f'epictetus/chapters/{n}.txt').read().split('\n')[0].strip():
        rows.append(f'{n} HEADING drift: {lines[0][:50]}'); bad+=1
    for l in lines[1:]:
        if assemble.is_subheading(l): rows.append(f'{n} SUBHEADING: {l[:55]}'); bad+=1
        if re.search(r'[*_#]', l): rows.append(f'{n} MARKUP: {l[:55]}'); bad+=1
done=len(list(pathlib.Path('epictetus/modern_chapters').glob('*.txt')))
print(f'{done}/101 files')
if rows:
    print('\n'.join(rows))
    # EXIT NONZERO, OR THE CHECK IS DECORATION. This printed its findings
    # and returned success for the first 48 files, so a real defect ("Why?"
    # at II.15, a bare question that renders as a section heading) rode
    # through a `check && commit` chain untouched. A checker that cannot
    # fail a build is a checker that will eventually be ignored.
    sys.exit(1)
print('ratios, headings, subheadings, markup: all clean')
