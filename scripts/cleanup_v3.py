"""
cleanup_v3.py — Produce formatted_v3.md from astathasa_rahasyam_formatted.md

Fixes applied:
1. Remove ## பக்கம்-N page marker headings (OCR page breaks become noise)
2. Remove bare inline numbers (e.g. "நில்லாது 18 இதுதான்") — no dot, just digit
3. Remove inline N. numbers mid-sentence (after Tamil vowel markers)
4. Join OCR hyphen line-breaks (word split across physical lines with "-")
5. Join lines that are clearly mid-word continuations of verse lines
   (e.g. "சிரியனரு" / "ளேது" → "சிரியனருளேது")
6. Split crammed sutras: "22. text 23. text" → separate lines
7. Remove orphan bare-number lines and book running-header lines
8. Normalise consecutive blank lines to max 1
"""

import re, os as _os

_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
IN  = _os.path.join(_ROOT, "sarvam_output", "astathasa_rahasyam_formatted.md")
OUT = _os.path.join(_ROOT, "sarvam_output", "astathasa_rahasyam_formatted_v3.md")

TAMIL = re.compile(r'[஀-௿]')
TAMIL_VOWEL_MARK = re.compile(r'[ா-ைொ-்ௗ]')  # ா-ை, ொ-்
SENTENCE_END = re.compile(r'[.!?|]$')

# ── Running page-header patterns ─────────────────────────────────────────────
BOOK_HEADERS = re.compile(
    r'^(?:\d{1,3}\s+)?(?:அஷ்டாதர\s*[ர]?ஹஸ்யம்|அஷ்டாதச\s*ரஹஸ்யம்|'
    r'அஷ்டாத[சஸ][ர]?\s*[ர]?ஹஸ்யம்|ஸ்ரீவசந\s*பூஷணம்|முமுக்ஷுப்படி|'
    r'தத்வத்ரயம்|அர்த்தபஞ்சகம்|தத்வபோகரம்|தத்தவபோகரம்|நவவிதஸம்பந்தம்|'
    r'ஸாரஸங்க்ரஹம்|ஸம்ஸாரஸாம்ராஜ்யம்|ப்ரமேயசேகரம்|'
    r'ப்ரபந்தரித்ராணம்|யாத்ருச்சிகப்படி|பரந்தபடி|'
    r'ஸ்ரீய:பதிப்படி|தத்த்வசோகரம்|தனித்வயம்|தனிசரமம்|'
    r'தனிப்ரணவம்)\s*(?:\d{1,3})?$',
    re.UNICODE
)

print(f"Reading {IN} ...")
with open(IN, encoding="utf-8") as f:
    raw = f.read()

lines = raw.split('\n')
print(f"  Input: {len(lines):,} lines, {len(raw):,} chars")

# ═══════════════════════════════════════════════════════════════════════════════
# PASS 1: Remove ## பக்கம்-N headings and running book-title headers
# ═══════════════════════════════════════════════════════════════════════════════
p1 = []
for line in lines:
    s = line.strip()
    # ## பக்கம்-N or ## பக்கம் N
    if re.match(r'^#{1,3}\s*பக்கம்[\s\-–—]*\d', s):
        continue
    # Standalone running book-title header (short line, matches known titles)
    if BOOK_HEADERS.match(s) and len(s) < 80:
        continue
    # Lone page numbers like "271" or "272 " at start of line (no Tamil)
    if re.match(r'^\d{1,3}\s*$', s) and not TAMIL.search(s):
        continue
    p1.append(line)

lines = p1

# ═══════════════════════════════════════════════════════════════════════════════
# PASS 2: Work on full text for inline regex fixes
# ═══════════════════════════════════════════════════════════════════════════════
text = '\n'.join(lines)

# 2a. Remove bare inline numbers (no dot) between Tamil words:
#     "நில்லாது 18 இதுதான்" → "நில்லாது இதுதான்"
#     Match: Tamil-char space(s) 1-3-digit(s) space(s) Tamil-char
#     Guard: NOT at start of line, NOT crossing newlines
text = re.sub(
    r'([஀-௿])[^\S\n]+\d{1,3}[^\S\n]+(?=[஀-௿])',
    r'\1 ',
    text
)

# 2b. Remove inline N. numbers mid-sentence after Tamil vowel markers:
#     "உபா 25. தேயம்" → "உபா தேயம்"  (only after vowel marker, not after '.')
text = re.sub(
    r'([ா-ைொ-்ௗ])[^\S\n]{0,2}\d{1,3}\.[^\S\n]+(?=[஀-௿])',
    r'\1 ',
    text
)

# 2c. Remove crammed inline sutra numbers within a line:
#     "22. text 23. text" → "22. text\n23. text"  (split to separate lines)
def split_crammed(text):
    pat = re.compile(
        r'(\d{1,3}\.\s+[^\n]{8,}?[஀-௿])\s+(\d{1,3}\.\s+[஀-௿])'
    )
    for _ in range(6):
        prev = text
        text = pat.sub(r'\1\n\2', text)
        if text == prev:
            break
    return text

text = split_crammed(text)

# ═══════════════════════════════════════════════════════════════════════════════
# PASS 3: Line-level: join OCR hyphen splits and mid-word verse continuations
# ═══════════════════════════════════════════════════════════════════════════════
lines = text.split('\n')
result = []
i = 0

# Tamil consonant cluster endings that indicate the word is incomplete
# (a Tamil consonant without a following vowel marker = pulli = halant)
# We detect this by checking if the line ends with a Tamil consonant followed
# by pulli (்) — meaning the OCR split the word right there.
ENDS_WITH_PULLI = re.compile(r'[க-ஹ]்$')   # consonant + ்
ENDS_WITH_CONSONANT = re.compile(r'[க-ஹ]$')      # bare consonant (no pulli/vowel)

SKIP_PREFIXES = ('#', '---', ':::', '>', '**', '- ', '* ', '!')

def is_skip(s):
    return not s or any(s.startswith(p) for p in SKIP_PREFIXES)

while i < len(lines):
    line = lines[i]
    s = line.rstrip()

    # Always pass through skip lines unchanged (headings, HR, fences, etc.)
    if is_skip(s.lstrip()) or s.lstrip().startswith('#'):
        result.append(line)
        i += 1
        continue

    nxt = lines[i + 1].strip() if i + 1 < len(lines) else ''
    nxt_ok = (nxt and TAMIL.search(nxt[0])
              and not is_skip(nxt)
              and not nxt.startswith('#')
              and not re.match(r'^\d{1,3}\.', nxt))

    # Case A: OCR hyphen split — "word-" + "continuation"
    # Only when hyphen follows a Tamil char (not a dash in text like "நீதி-வழுவாச்")
    if (s.endswith('-') and len(s) > 4
            and TAMIL.search(s[-2])
            and nxt_ok):
        result.append(s[:-1] + nxt)
        i += 2
        continue

    # Case B: Line ends with Tamil consonant+pulli (்) — definitely incomplete
    if ENDS_WITH_PULLI.search(s) and nxt_ok:
        result.append(s + nxt)   # no space: pulli means next char continues the word
        i += 2
        continue

    # Case C: Line ends with bare Tamil consonant (no vowel, no pulli) → incomplete
    # but only for SHORT lines (verse half-lines), not long prose lines
    if (ENDS_WITH_CONSONANT.search(s)
            and len(s) < 50
            and not SENTENCE_END.search(s)
            and nxt_ok
            and not re.match(r'^\d{1,3}\.', nxt)):
        result.append(s + nxt)   # no space: consonant continues directly
        i += 2
        continue

    result.append(line)
    i += 1

text = '\n'.join(result)

# ═══════════════════════════════════════════════════════════════════════════════
# PASS 4: Remove orphan number-only lines
# ═══════════════════════════════════════════════════════════════════════════════
lines = text.split('\n')
p4 = []
for line in lines:
    s = line.strip()
    if re.match(r'^\d{1,3}\.\s*$', s):   # lone "14." line
        continue
    p4.append(line)
lines = p4

# ═══════════════════════════════════════════════════════════════════════════════
# PASS 5: Collapse excessive blank lines (max 1 consecutive blank line)
# ═══════════════════════════════════════════════════════════════════════════════
text = '\n'.join(lines)
text = re.sub(r'\n{3,}', '\n\n', text)

# ═══════════════════════════════════════════════════════════════════════════════
# Write output
# ═══════════════════════════════════════════════════════════════════════════════
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(text)

out_lines = text.count('\n')
print(f"  Output: {len(text):,} chars, {out_lines:,} lines")
print(f"Done: {OUT}")
