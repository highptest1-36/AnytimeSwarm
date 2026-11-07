#!/usr/bin/env bash
# Build main.pdf and supplementary.pdf of the Elsevier manuscript and report problems.
cd "$(dirname "$0")/.." || exit 1
run() { pdflatex -interaction=nonstopmode "$1" >/dev/null 2>&1; }
run main; bibtex main >/dev/null 2>&1
run supplementary; bibtex supplementary >/dev/null 2>&1
run supplementary; run main; run main; run supplementary
for f in main supplementary; do
  echo "== $f"
  grep -n "^!" $f.log | sort | uniq -c | head -8
  echo "overfull hbox > 1pt: $(grep 'Overfull \\hbox' $f.log | grep -v 'output is active' | grep -vc '(0\.[0-9]*pt')"
  grep "Reference.*undefined\|Citation.*undefined" $f.log | sort -u | head -8
done
python -c "
import fitz
for f in ['main.pdf', 'supplementary.pdf']:
    d = fitz.open(f); t = ''.join(p.get_text() for p in d)
    print(f, len(d), 'pages; TODO:', t.count('TODO'), '; ??:', t.count('??'))
"
