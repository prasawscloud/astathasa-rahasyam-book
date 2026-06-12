"""
cleanup_v2.py  —  Clean astathasa_rahasyam_formatted.md → formatted_v2.md

Problems fixed:
1. Inline OCR line-numbers mid-sentence: "word 25. continuation" → "word continuation"
   These are physical page line-numbers OCR picked up. Distinguished from real sutra
   numbers by: the preceding text ends mid-word (no sentence-ending punctuation).
2. Running page headers: "86 அஷ்டாதர ரஹஸ்யம்" / "ஸ்ரீவசநூஷணம் 87" standalone lines → removed
3. Sutras split across lines: "1. text 2. more text" on a single line → split to separate lines
4. Blank line normalisation: max 1 blank line between content
"""

import re, os as _os

_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
IN  = _os.path.join(_ROOT, "sarvam_output", "astathasa_rahasyam_formatted.md")
OUT = _os.path.join(_ROOT, "sarvam_output", "astathasa_rahasyam_formatted_v2.md")

TAMIL = re.compile(r'[஀-௿]')
SENTENCE_END = re.compile(r'[.!?।॥।॥]$')

# Running page-header patterns (standalone lines only)
# Matches: "BookTitle NNN" or "NNN BookTitle" as standalone lines (running headers)
BOOK_TITLES = re.compile(
    r'^(?:\d{1,3}\s+)?(?:அஷ்டாதர\s*ஹஸ்யம்|அஷ்டாதச\s*ரஹஸ்யம்|'
    r'அஷ்டாத[சஸ][ர]?\s*ஹஸ்யம்|ஸ்ரீவசந\s*பூஷணம்|முமுக்ஷுப்படி|'
    r'தத்வத்ரயம்|அர்த்தபஞ்சகம்|தத்வபோகரம்|தத்தவபோகரம்|நவவிதஸம்பந்தம்|'
    r'ஸாரஸங்க்ரஹம்|ஸம்ஸாரஸாம்ராஜ்யம்|ப்ரமேயசேகரம்|'
    r'ப்ரபந்தரித்ராணம்|யாத்ருச்சிகப்படி|பரந்தபடி|'
    r'ஸ்ரீய:பதிப்படி|தத்த்வசோகரம்|தனித்வயம்|தனிசரமம்|'
    r'தனிப்ரணவம்)\s*(?:\d{1,3})?$'
)

print(f"Reading {IN}…")
with open(IN, encoding="utf-8") as f:
    text = f.read()

lines = text.split('\n')
print(f"  {len(lines):,} lines, {len(text):,} chars")

# ── Pass 1: Remove standalone running page headers ────────────────────────────
cleaned = []
for line in lines:
    s = line.strip()
    # Skip standalone book-title / page-number header lines
    if BOOK_TITLES.match(s) and len(s) < 80:
        continue
    cleaned.append(line)
lines = cleaned

# ── Pass 2: Join lines where OCR split mid-word, then merge inline line-numbers ─
# Strategy: work on the joined text.
# An inline line-number looks like: Tamil-text-ending-mid-word, space, "N.", space, more-Tamil
# i.e. the char before "N." is NOT a sentence-ending punctuation.
# We collapse: "word 25. continuation" → "word continuation"

text = '\n'.join(lines)

# Pattern: a Tamil char (or closing paren/quote), optional space, then "N. " where N<=3 digits,
# followed by more Tamil — but NOT at start of line (those are real sutras)
# We only remove mid-line numbers where the preceding context ends mid-word.

def remove_inline_numbers(text):
    # Remove inline OCR page-line numbers that appear mid-sentence.
    # These appear after Tamil chars, punctuation (. , ; : " "), or closing parens.
    # Pattern: (non-newline context char) optional-space N. space Tamil-char
    # Do NOT remove when preceded by newline (start of line = real sutra number).
    pattern = re.compile(
        r'([஀-௿ா-்\)\"\.\,\;\:\"\'"])\s{0,3}\d{1,3}\.\s+(?=[஀-௿\"])'
    )
    return pattern.sub(r'\1 ', text)

text = remove_inline_numbers(text)

# ── Pass 3: Split multiple sutras crammed on one line ────────────────────────
# Pattern: "N. text M. text" where both N and M are sutra numbers and there's Tamil between them
# Only at start of line or after previous sutra

def split_crammed_sutras(text):
    # "1. blah blah 2. more blah" → "1. blah blah\n2. more blah"
    # Match: digit(s) dot space Tamil-content space digit(s) dot space
    # But be careful not to split footnote references like "a 1. quote"
    pattern = re.compile(
        r'(\d{1,3}\.\s+[^.\n]{10,}?[஀-௿])\s+(\d{1,3}\.\s+[஀-௿])'
    )
    # Run multiple times to catch chains
    for _ in range(5):
        prev = text
        text = pattern.sub(r'\1\n\2', text)
        if text == prev:
            break
    return text

text = split_crammed_sutras(text)

# ── Pass 4: Remove orphan number-only lines (e.g. a lone "14." or "15." line) ──
lines = text.split('\n')
cleaned = []
for line in lines:
    s = line.strip()
    # A line that is ONLY a number with dot and no Tamil content → remove
    if re.match(r'^\d{1,3}\.\s*$', s):
        continue
    # A line that is ONLY digits (like "42" standalone = page continuation number) → remove
    # but only if short and no Tamil
    if re.match(r'^\d{1,3}$', s) and not TAMIL.search(s):
        continue
    cleaned.append(line)
lines = cleaned

# ── Pass 5: Collapse excessive blank lines (max 1 consecutive blank) ──────────
text = '\n'.join(lines)
text = re.sub(r'\n{3,}', '\n\n', text)

# ── Pass 6: Fix lines where a sentence continues after a mid-word break ───────
# Lines that end with a Tamil char (no punctuation) and next line starts mid-word
# (lowercase Tamil continuation — no heading marker)
lines = text.split('\n')
result = []
i = 0
while i < len(lines):
    line = lines[i]
    s = line.rstrip()

    # Skip headings, blank, HR, fences
    if (not s or s.startswith('#') or s.startswith('---')
            or s.startswith(':::') or s.startswith('>')
            or s.startswith('**') or s.startswith('- ')
            or s.startswith('*') or s.startswith('!')):
        result.append(line)
        i += 1
        continue

    # Check if line ends mid-word (Tamil char, no sentence-end punctuation)
    last = s[-1] if s else ''
    hyphen_join = last == '-' and len(s) > 10
    ends_mid = ((TAMIL.search(last) or last in ')') and not SENTENCE_END.search(s)) or hyphen_join
    # Don't join very short lines (labels/headings)
    if len(s) < 20:
        ends_mid = False

    if ends_mid and i + 1 < len(lines):
        nxt = lines[i + 1].strip()
        # Join if next line starts with Tamil/quote and isn't a heading/sutra/blank/fence
        if (nxt and (TAMIL.search(nxt[0]) or nxt[0] in '"\'|')
                and not nxt.startswith('#')
                and not nxt.startswith('---')
                and not nxt.startswith(':::')
                and not re.match(r'^\d{1,3}\.', nxt)):
            if hyphen_join:
                # Remove the trailing hyphen before joining (OCR line-wrap hyphen)
                result.append(s[:-1] + nxt)
            else:
                result.append(s + ' ' + nxt)
            i += 2
            continue

    result.append(line)
    i += 1

text = '\n'.join(result)

# ── Final: collapse blanks again after joins ──────────────────────────────────
text = re.sub(r'\n{3,}', '\n\n', text)

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(text)

out_lines = text.count('\n')
print(f"  Output: {len(text):,} chars, {out_lines:,} lines")
print(f"Done → {OUT}")
