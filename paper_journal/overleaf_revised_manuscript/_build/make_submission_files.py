"""Separate files that the AST guide for authors asks for, written to ../AST_submission_files:
figures as separate vector files (Figure_1 ...), highlights and vitae as editable Word files, the supplementary PDF.
Run from the overleaf folder after a full build: python _build/make_submission_files.py"""
import re
import shutil
from pathlib import Path

from docx import Document
from docx.shared import Cm, Pt

HERE = Path(__file__).resolve().parents[1]
OUT = HERE.parents[0] / "AST_submission"   # flat folder written by flatten.py (figures are copied there)
OUT.mkdir(exist_ok=True)

# numbers of the highlights from the generated macros
macros = {}
for f in (HERE / "tables").glob("numbers*.tex"):
    for m in re.finditer(r"\\csname v(\w+)\\endcsname\{([^}]*)\}", f.read_text(encoding="utf-8")):
        macros[m.group(1)] = m.group(2)
front = (HERE / "_build" / "front.tex").read_text(encoding="utf-8")
items = re.findall(r"\\item (.*)", front.split(r"\begin{highlights}")[1].split(r"\end{highlights}")[0])
highlights = []
for it in items:
    it = re.sub(r"\\val\{(\w+)\}", lambda m: macros[m.group(1)], it).replace(r"\%", "%")
    highlights.append(it)
for h in highlights:
    assert len(h) <= 85, (len(h), h)

doc = Document()
doc.add_heading("Highlights", level=1)
for h in highlights:
    doc.add_paragraph(h, style="List Bullet")
doc.save(OUT / "Highlights.docx")

IEEE = HERE.parents[0] / "ieee"
VITAE = [
    ("Cao-Phuc Ha", IEEE / "author2.jpg",
     "Cao-Phuc Ha is currently pursuing the B.S. degree in Artificial Intelligence at FPT University, Vietnam. His "
     "research interests include artificial intelligence and robotics, with applications to autonomous vehicles, "
     "drones and unmanned aerial systems."),
    ("Vu Minh Anh Nguyen", HERE.parents[2] / "Miaiu.jpg",
     "Vu Minh Anh Nguyen is currently pursuing the B.S. degree in Artificial Intelligence at FPT University, Ho Chi "
     "Minh City, Vietnam. Her research interests include artificial intelligence, machine learning, computer vision "
     "and deep learning. Her current research focuses on developing robust, efficient and practical AI models for "
     "real-world applications, particularly in visual perception and intelligent systems."),
    ("Duong Thanh Tran", None,
     "Duong Thanh Tran is with the Department of Integrative Biotechnology, College of Biotechnology and "
     "Bioengineering, Sungkyunkwan University, Suwon, Republic of Korea."),
    ("Phu-Nguyen Le", IEEE / "thay_Nguyen.jpg",
     "Phu-Nguyen Le received the B.S. degree in electrical engineering from Da Nang University of Technology, "
     "Vietnam, in 2012, and the Ph.D. degree from the University of Ulsan, South Korea, in 2021. He is currently with "
     "the Faculty of Electrical and Electronics Engineering, Vietnam Aerospace University. His research interests "
     "include sensor-based robotic applications, robot calibration and AI-based robotic control."),
]
doc = Document()
doc.add_heading("Vitae", level=1)
for name, photo, text in VITAE:
    doc.add_heading(name, level=2)
    if photo and photo.exists():
        doc.add_picture(str(photo), width=Cm(2.5))
    else:
        doc.add_paragraph("[photograph to be added]")
    p = doc.add_paragraph(text)
    p.runs[0].font.size = Pt(11)
    assert len(text.split()) <= 100
doc.save(OUT / "Vitae.docx")

shutil.copy(HERE / "supplementary.pdf", OUT / "Supplementary_material.pdf")
for h in highlights:
    print(len(h), h)
print("files:", sorted(p.name for p in OUT.iterdir()))
