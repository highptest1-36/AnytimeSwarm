"""references_ast.bib: copy of ../../references.bib with journal names abbreviated according to the ISO 4 List of
Title Word Abbreviations (LTWA), as the guide for authors of Aerospace Science and Technology asks. Nothing else
changes. Run from the overleaf folder: python _build/make_bib.py"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
SRC = HERE.parents[0] / "references.bib"
LTWA = {
    "AI Communications": "AI Commun.",
    "AI Magazine": "AI Mag.",
    "Applied Sciences": "Appl. Sci.",
    "Artificial Intelligence": "Artif. Intell.",
    "Autonomous Robots": "Auton. Robots",
    r"Computers \& Industrial Engineering": "Comput. Ind. Eng.",
    r"Computers \& Operations Research": "Comput. Oper. Res.",
    "EURO Journal on Transportation and Logistics": "EURO J. Transp. Logist.",
    "European Journal of Operational Research": "Eur. J. Oper. Res.",
    "Expert Systems": "Expert Syst.",
    "IEEE Transactions on Computers": "IEEE Trans. Comput.",
    "IEEE Transactions on Robotics": "IEEE Trans. Robot.",
    "International Journal of Production Economics": "Int. J. Prod. Econ.",
    "International Journal of Production Research": "Int. J. Prod. Res.",
    "International Transactions in Operational Research": "Int. Trans. Oper. Res.",
    r"Journal of Intelligent \& Robotic Systems": "J. Intell. Robot. Syst.",
    "Journal of Scheduling": "J. Sched.",
    r"Manufacturing \& Service Operations Management": "Manuf. Serv. Oper. Manag.",
    "ORSA Journal on Computing": "ORSA J. Comput.",
    "Operations Research": "Oper. Res.",
    "Pattern Recognition Letters": "Pattern Recognit. Lett.",
    "Robotics and Autonomous Systems": "Robot. Auton. Syst.",
    "Scandinavian Journal of Statistics": "Scand. J. Stat.",
    "Science Robotics": "Sci. Robot.",
    "The International Journal of Robotics Research": "Int. J. Robot. Res.",
    "Transportation Research Part C: Emerging Technologies": "Transp. Res. Part C Emerg. Technol.",
    "Transportation Science": "Transp. Sci.",
}
# unchanged (single word or already an abbreviation): 4OR, Aerospace, Drones, IEEE Access, Networks, OR Spectrum, Science

text = SRC.read_text(encoding="utf-8")
n = 0
def repl(m):
    global n
    name = m.group(2)
    if name in LTWA:
        n += 1
        return m.group(1) + LTWA[name] + m.group(3)
    return m.group(0)
text = re.sub(r"(journal\s*=\s*\{)(.*?)(\})", repl, text)
(HERE / "references_ast.bib").write_text(text, encoding="utf-8", newline="\n")
print("abbreviated", n, "journal fields")
