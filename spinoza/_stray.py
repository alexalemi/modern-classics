import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import structure as S

t = dict(S.split_parts(S.body()))[3]
i = t.find("is evident from Ax")
print("SOURCE:", repr(re.sub(r"\s+", " ", t[i - 110:i + 190])))
m = (pathlib.Path(__file__).resolve().parent / "chapters" / "008.txt").read_text()
j = m.find("evident from Ax")
print()
print("OUTPUT:", repr(re.sub(r"\s+", " ", m[j - 110:j + 190])))
