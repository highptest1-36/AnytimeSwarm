"""Write the generated reference lists (main.bbl, supplementary.bbl; elsarticle-num) into main.tex and
supplementary.tex as thebibliography, as in the template, so that both compile without BibTeX.
Run after a full build: python _build/inline_bbl.py"""
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
OLD = "\\bibliographystyle{elsarticle-num}\n\\bibliography{references_ast}\n"
NOTE = ("% Reference list generated with BibTeX (style elsarticle-num, references_ast.bib with LTWA journal\n"
        "% abbreviations) and pasted here; regenerate with the scripts in _build/.\n")
for name in ["main", "supplementary"]:
    tex = (HERE / f"{name}.tex").read_text(encoding="utf-8")
    if OLD not in tex:
        print(name, ": already inlined")
        continue
    bbl = (HERE / f"{name}.bbl").read_text(encoding="utf-8").strip()
    (HERE / f"{name}.tex").write_text(tex.replace(OLD, NOTE + bbl + "\n"), encoding="utf-8", newline="\n")
    print(name, ": inlined", bbl.count("\\bibitem"), "references")
