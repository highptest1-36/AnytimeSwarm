"""Assemble the Elsevier (cas-dc) manuscript main.tex from the IEEE section sources without changing their content.

Only format changes are made:
- figure placement options in the cas syntax ([pos=t]),
- wide generated tables as table* (two-column layout),
- small fractions in display equations written with a solidus, as the AST guide for authors asks,
- Elsevier front matter (_build/front.tex) and end matter (_build/back.tex),
- references with elsarticle-num and LTWA journal abbreviations (references_ast.bib).
Run from the overleaf folder: python _build/assemble.py  (then pdflatex/bibtex; python _build/inline_bbl.py)
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
IEEE = HERE.parents[0] / "ieee" / "sections"
BUILD = HERE / "_build"

SECTIONS = ["introduction", "related", "problem", "method", "setup", "results", "discussion", "conclusion"]
WIDE_TABLES = ["tab_related", "tab_hyp", "tabm_s4", "tabm_s5", "tabm_s6"]

REPLACE = [  # (old, new, expected count)
    (r"p\ \ge\ \theta_j=\frac{c_j}{w_j+c_j}.", r"p\ \ge\ \theta_j=c_j/(w_j+c_j).", 1),
    (r"u_\lambda=U-\lambda\,\frac{n_{\mathrm{late}}}{n},\qquad u^w_\lambda=U-\lambda\,\frac{R_{\mathrm{late}}}{R},",
     r"u_\lambda=U-\lambda\,n_{\mathrm{late}}/n,\qquad u^w_\lambda=U-\lambda\,R_{\mathrm{late}}/R,", 1),
]


def body():
    parts = []
    for s in SECTIONS:
        t = (IEEE / f"{s}.tex").read_text(encoding="utf-8")
        t = t.replace(r"\begin{figure*}[t]", r"\begin{figure*}[pos=t]")
        t = t.replace(r"\begin{figure}[t]", r"\begin{figure}[pos=t]")
        parts.append(f"%%{'=' * 61}%%\n" + t.rstrip() + "\n")
    out = "\n".join(parts)
    for old, new, n in REPLACE:
        if out.count(old) != n:
            raise SystemExit(f"expected {n} x {old!r}, found {out.count(old)}")
        out = out.replace(old, new)
    return out


def abstract():
    t = (IEEE / "abstract.tex").read_text(encoding="utf-8")
    return t.split(r"\begin{abstract}", 1)[1].split(r"\end{abstract}", 1)[0].strip()


def wide_tables():
    for name in WIDE_TABLES:
        p = HERE / "tables" / f"{name}.tex"
        t = p.read_text(encoding="utf-8")
        t = re.sub(r"\\begin\{table\}\[[^\]]*\]", r"\\begin{table*}[t]", t)
        t = t.replace(r"\end{table}", r"\end{table*}")
        p.write_text(t, encoding="utf-8", newline="\n")


def main():
    wide_tables()
    front = (BUILD / "front.tex").read_text(encoding="utf-8").replace("%%ABSTRACT%%", abstract())
    back = (BUILD / "back.tex").read_text(encoding="utf-8")
    tex = (front + body() + back
           + "\n\\bibliographystyle{elsarticle-num}\n\\bibliography{references_ast}\n\n\\end{document}\n")
    (HERE / "main.tex").write_text(tex, encoding="utf-8", newline="\n")
    print("main.tex written:", len(tex.splitlines()), "lines")


if __name__ == "__main__":
    main()
