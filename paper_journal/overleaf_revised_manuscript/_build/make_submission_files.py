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

def word_doc():
    d = Document()
    st = d.styles["Normal"]
    st.font.name = "Times New Roman"
    st.font.size = Pt(11.5)
    for s in d.sections:
        s.left_margin = s.right_margin = Cm(2.5)
        s.top_margin = s.bottom_margin = Cm(2.2)
    return d


# declaration of competing interests (same wording as the Elsevier declarations tool, option "nothing to declare")
doc = word_doc()
doc.add_heading("Declaration of interests", level=1)
doc.add_paragraph("Manuscript title: Chance Constraints as Effective Deadlines for Fast Replanning of UAV Fleets Under "
                  "Uncertainty")
doc.add_paragraph("☒ The authors declare that they have no known competing financial interests or personal "
                  "relationships that could have appeared to influence the work reported in this paper.")
doc.add_paragraph("☐ The authors declare the following financial interests/personal relationships which may be "
                  "considered as potential competing interests:")
doc.save(OUT / "Declaration_of_competing_interests.docx")

# cover letter
M = lambda k: macros[k].lstrip("+")
TITLE = "Chance Constraints as Effective Deadlines for Fast Replanning of UAV Fleets Under Uncertainty"
doc = word_doc()
for line in ("Phu-Nguyen Le", "Faculty of Electrical and Electronics Engineering", "Vietnam Aerospace University",
             "Ho Chi Minh City, 700000, Vietnam", "nguyenlp@vaa.edu.vn"):
    doc.add_paragraph(line).paragraph_format.space_after = Pt(0)
doc.add_paragraph()
doc.add_paragraph("To the Editor-in-Chief, Aerospace Science and Technology")
doc.add_paragraph("Dear Editor,")
body = [
    f"On behalf of all authors, I submit the manuscript entitled “{TITLE}” for consideration as a research "
    "article in Aerospace Science and Technology.",
    "Teams of unmanned aerial vehicles must repair their plans within a fraction of a second when tasks arrive or "
    "vehicles fail, while wind, speed and service-time errors make the tasks late in a route miss their deadlines. "
    "The manuscript proposes LTCC, a replanner that turns a chance constraint on the finish time of every task into a "
    "closed-form effective deadline, so that fast routing heuristics and auction-based allocators are reused "
    "unchanged. A cost-aware fallback uses the probability of meeting the deadline to decide which risky tasks are "
    "still worth attempting, again in closed form and without tuning for the cost of a late arrival.",
    "The method is evaluated in seven studies on held-out missions, each with a protocol fixed in advance, in a "
    "kinematic simulator and in PX4 software-in-the-loop flights with Gazebo and ROS 2. LTCC served "
    f"{M('XDabsFortyAll')} percentage points more reward than the nominal model and {M('WURelCACBBA')}% more than the "
    "consensus-based bundle algorithm. With a late cost of one task reward, the cost-aware fallback scored "
    f"{M('FAbsCCfbOne')} points above the nominal fallback, and in the software-in-the-loop flights the fallback "
    f"raised the utility by {M('HURelNoFb')}%.",
    "We believe that the work fits the scope of the journal in robotics and intelligent systems, decision aid and air "
    "transport systems, as it addresses the reliable operation of UAV fleets under execution uncertainty.",
    "We confirm that this manuscript is original, has not been published previously and is not under consideration "
    "for publication elsewhere. All authors have approved the manuscript and agree with its submission. The authors "
    "declare no competing interests, and the research received no specific funding. The code, frozen protocols and "
    "raw results are available at https://github.com/highptest1-36/AnytimeSwarm, and supplementary material is "
    "provided with the submission.",
    "Thank you for your consideration. We look forward to hearing from you.",
]
for t in body:
    p = doc.add_paragraph(t)
    p.paragraph_format.space_after = Pt(8)
doc.add_paragraph("Sincerely,")
for line in ("Phu-Nguyen Le (corresponding author)", "on behalf of Cao-Phuc Ha, Vu Minh Anh Nguyen and Duong Thanh "
             "Tran"):
    doc.add_paragraph(line).paragraph_format.space_after = Pt(0)
doc.save(OUT / "Cover_letter.docx")

shutil.copy(HERE / "supplementary.pdf", OUT / "Supplementary_material.pdf")
for h in highlights:
    print(len(h), h)
print("files:", sorted(p.name for p in OUT.iterdir()))
