"""Supplementary material for the Elsevier submission: the body of ../ieee/supplementary.tex unchanged, in a plain
single-column article layout, with references to the labels of main.tex (same folder) and the AST reference style.
Run from the overleaf folder: python _build/make_supp.py"""
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
SRC = HERE.parents[0] / "ieee" / "supplementary.tex"

HEADER = r"""% Supplementary material of the LTCC manuscript (Aerospace Science and Technology submission).
% Build after main.tex: pdflatex supplementary && bibtex supplementary && pdflatex supplementary (x2)
% Every number comes from the generated tables/numbers*.tex files; none is typed by hand.
\documentclass[a4paper,10pt]{article}
\usepackage[margin=2.2cm]{geometry}
\usepackage[T1]{fontenc}
\usepackage{amsmath}
\usepackage{newtxtext,newtxmath}
\usepackage[numbers]{natbib}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{threeparttable}
\usepackage{array}
\usepackage{xcolor}
\usepackage{xr-hyper}
\usepackage[hidelinks]{hyperref}
\externaldocument{main}
% propositions and proofs in upright type
\newcounter{prop}
\renewcommand{\theprop}{S\arabic{prop}}
\newenvironment{prop}{\par\smallskip\refstepcounter{prop}\noindent Proposition~\theprop.\ }{\par\smallskip}
\providecommand{\QED}{\hfill$\blacksquare$}
\newenvironment{proof}{\par\noindent Proof.\ }{\QED\par}
\newcommand{\todo}[1]{\textcolor{red}{[TODO: #1]}}
\newcommand{\mname}{LTCC}  % name of the proposed method
\newcommand{\val}[1]{\ifcsname v#1\endcsname\csname v#1\endcsname\else\todo{#1}\fi}
\makeatletter
\@for\@numfile:=static_numbers,static_numbers_XL,static_numbers_scale,numbers,numbers_s2,numbers_s3,numbers_s3x,%
numbers_err,numbers_s4,numbers_s4c,numbers_s4x,numbers_s4cx,numbers_latepen,numbers_s5,numbers_s6,numbers_extra,%
numbers_demo,numbers_robust,numbers_calib,numbers_s7,numbers_s7x,numbers_s7c\do{%
  \IfFileExists{tables/\@numfile.tex}{\input{tables/\@numfile.tex}}{}}
\makeatother
\newsavebox{\ltccfigbox}
\newcommand{\fig}[2]{\sbox{\ltccfigbox}{\includegraphics{figures/#1.pdf}}%
  \ifdim\wd\ltccfigbox>\linewidth\resizebox{\linewidth}{!}{\usebox{\ltccfigbox}}\else\usebox{\ltccfigbox}\fi}
\newcommand{\uprighttext}{\def\textbf##1{##1}\def\textit##1{##1}}
\newcommand{\inputtable}[1]{\begingroup\uprighttext\input{tables/#1.tex}\endgroup}
\renewcommand{\thesection}{S\arabic{section}}
\renewcommand{\thesubsection}{\thesection.\arabic{subsection}}
\renewcommand{\thetable}{S\arabic{table}}
\renewcommand{\thefigure}{S\arabic{figure}}
\renewcommand{\theequation}{S\arabic{equation}}

\begin{document}
\title{Supplementary material for: Chance Constraints as Effective Deadlines for Fast Replanning of UAV Fleets Under Uncertainty}
\author{Cao-Phuc Ha, Vu Minh Anh Nguyen, Duong Thanh Tran, and Phu-Nguyen Le}
\date{}
\maketitle
"""

src = SRC.read_text(encoding="utf-8")
body = src.split(r"\maketitle", 1)[1]
body = body.replace(r"\bibliographystyle{IEEEtran}", r"\bibliographystyle{elsarticle-num}")
body = body.replace(r"\bibliography{../references}", r"\bibliography{references_ast}")
(HERE / "supplementary.tex").write_text(HEADER + body, encoding="utf-8", newline="\n")
print("supplementary.tex written")
