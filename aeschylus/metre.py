"""A METRE WITNESS FOR THE SUNG/SPOKEN RULING: count syllables per line.

Perseus' division labels are the only witness prep.py has for whether a
speech is sung or spoken, and for Aeschylus they are wrong in about
thirty places. This is the SECOND witness, and it shares no code with the
first: it counts vowel groups in the Greek. Measured over Aeschylus,
spoken lines run 12-13 syllables (90%; iambic trimeter is 12, with
resolutions), trochaic tetrameter 15-16, and lyric mostly 6-11. So a
speech of two or more lines that are ALL 12-15 syllables inside a lyric
division is almost certainly iambic trimeter, and a run of short lines
inside an episode is lyric.

It is a WITNESS, not a rule: every disagreement it reports was read
before it became a KIND_FIX (Cassandra's stanzas mix trimeter and lyric
inside one speech and stay sung; a two-line lyric close can be 12/14).
What it caught that nothing else could: a bug that made every speech
after a fix inherit the fix, and six mislabelled passages. Run it after
any change to prep.KIND_FIXES and read the list.

    python3 aeschylus/metre.py
"""
import sys, re, unicodedata, collections, xml.etree.ElementTree as ET
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import prep
V=set("αεηιουωᾳῃῳ")
def strip(s):
    # keep the iota subscript (a vowel) and the DIAERESIS (U+0308), which
    # marks that two adjacent vowels are NOT a diphthong: "naian" with the
    # mark is three syllables, without it two, and the undercount made the
    # Messenger's trimeters at Medea 1121-1123 read as lyric.
    s=unicodedata.normalize('NFD',s)
    return ''.join(c for c in s if not unicodedata.combining(c) or c in 'ͅ\u0308').lower()
DIPH={"αι","ει","οι","υι","αυ","ευ","ου","ηυ","ωυ"}
def syl(line):
    s=strip(line); s=re.sub(r"[^α-ῳ \u0308]"," ",s)
    n=0; i=0; s=s.replace(" ","")
    while i<len(s):
        if s[i] in V or s[i]=='ͅ':
            if (i+1<len(s) and s[i:i+2] in DIPH
                    and not (i+2<len(s) and s[i+2]=='\u0308')):
                i+=2
            else: i+=1
            n+=1
        else: i+=1
    return n
def num(s):
    d=''.join(c for c in (s or '') if c.isdigit()); return int(d) if d else -1
def looks_spoken(ls, thresh=0.85):
    counts=[syl(t) for _,t in ls if len(t.split())>=2]
    if len(counts)<2: return None
    return sum(1 for c in counts if 12<=c<=15)/len(counts) >= thresh
def validate():
    conf=collections.Counter(); wrong=[]
    for n,title,date,eng in prep.PLAYS:
        g=prep.stream(prep.fetch(n,"grc2"),play=n)
        for kind,name,ls,st in g:
            v=looks_spoken(ls)
            if v is None: continue
            actual=not prep.is_sung(kind)
            conf[(actual,v)]+=1
            if actual!=v: wrong.append((title,name,ls[0][0],ls[-1][0],len(ls),'spoken' if actual else 'sung',[syl(t) for _,t in ls][:8]))
    print(conf)
    for w in wrong: print('  ',w)
if __name__=="__main__":
    validate()
