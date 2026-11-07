"""Authors' style: plain hyphens instead of en dashes. Replaces the LaTeX en dash `--` (not `---`) and the Unicode
en dash with `-` in non-comment lines of the given files (main.tex, supplementary.tex, tables/*.tex, supp/*.tex).
Run from the overleaf folder: python _build/hyphens.py"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
PAT = re.compile(r"(?<!-)--(?!-)")


def fix(path):
    lines = path.read_text(encoding="utf-8").split("\n")
    out, n = [], 0
    for ln in lines:
        if ln.lstrip().startswith("%"):
            out.append(ln)
            continue
        new = PAT.sub("-", ln).replace("–", "-")
        n += new != ln
        out.append(new)
    if n:
        path.write_text("\n".join(out), encoding="utf-8", newline="\n")
    return n


files = [HERE / "main.tex", HERE / "supplementary.tex"] + sorted((HERE / "tables").glob("*.tex")) \
    + sorted((HERE / "supp").glob("*.tex"))
total = sum(fix(f) for f in files if f.exists())
print("lines changed:", total)
