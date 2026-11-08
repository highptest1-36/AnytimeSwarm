"""Upload folder for the AST submission: exactly the files to upload, nothing else.
Copies from ../AST_submission (built by flatten.py and make_submission_files.py) to ../AST_upload and checks that
main.tex compiles there (in a temporary copy, so no build files are left behind).
Run from the overleaf folder after a full build: python _build/make_upload.py"""
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
SRC = HERE.parents[0] / "AST_submission"
OUT = HERE.parents[0] / "AST_upload"

FILES = (["main.tex", "cas-dc.cls", "cas-common.sty", "cas-email.jpeg"]
         + ["Figure_1.pdf", "Figure_2.pdf", "Figure_3.pdf", "Figure_4a.pdf", "Figure_4b.pdf",
            "Figure_5.pdf", "Figure_6.pdf", "Figure_7.pdf", "Figure_8.pdf"]
         + ["Highlights.docx", "Supplementary_material.pdf", "Cover_letter.docx",
            "Declaration_of_competing_interests.docx"])

if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir()
for f in FILES:
    shutil.copy2(SRC / f, OUT / f)

# compile check in a temporary copy
with tempfile.TemporaryDirectory() as tmp:
    for f in FILES:
        shutil.copy2(OUT / f, Path(tmp) / f)
    for _ in range(2):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "main.tex"], cwd=tmp, capture_output=True)
    log = (Path(tmp) / "main.log").read_text(encoding="latin-1")
    errors = sum(1 for line in log.splitlines() if line.startswith("!"))
    undefined = log.count("undefined")
    pages = subprocess.run(["pdfinfo", "main.pdf"], cwd=tmp, capture_output=True, text=True).stdout
    pages = [l for l in pages.splitlines() if l.startswith("Pages")]
    print("compile check: errors", errors, "undefined", undefined, pages)
    assert errors == 0 and undefined == 0

print("written", OUT)
for p in sorted(OUT.iterdir()):
    print(f"  {p.name:45s} {p.stat().st_size / 1024:8.1f} KB")
