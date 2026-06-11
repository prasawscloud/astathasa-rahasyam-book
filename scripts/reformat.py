"""
Reformat astathasa_rahasyam_tamil_full.md into a clean, properly structured book.

Problems fixed:
1. Paragraphs split across lines (OCR line-wrap) → join into single paragraphs
2. Page header/footer lines leaked into body (e.g. "தத்வத்ரயம் 31") → removed
3. Inline HTML table markup in TOC → converted to clean markdown
4. Roman-numeral continuation headings (## II, ## III …) → removed, text joined
5. OCR corruption commas mid-word (e.g. அஷ்டாத,ர → அஷ்டாதச) → cleaned
6. Duplicate footnote reference lines → deduplicated
7. Footnote anchors (##### a ...) → formatted as blockquotes
8. Numbered sūtra paragraphs → kept but rejoined properly
"""

import re, sys, unicodedata

import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
IN  = _os.path.join(_ROOT, "sarvam_output", "astathasa_rahasyam_tamil_full.md")
OUT = _os.path.join(_ROOT, "sarvam_output", "astathasa_rahasyam_formatted.md")

print("Reading source file…")
with open(IN, encoding="utf-8") as f:
    text = f.read()

print(f"  Source: {len(text):,} chars, {text.count(chr(10)):,} lines")

# ── 1. Normalise line endings ──────────────────────────────────────────────
text = text.replace("\r\n", "\n").replace("\r", "\n")

# ── 2. Remove raw HTML tables; convert to plain text list ─────────────────
def html_table_to_md(m):
    """Convert <table> block to a simple markdown list."""
    rows = re.findall(r'<tr>(.*?)</tr>', m.group(0), re.DOTALL)
    lines = []
    for row in rows:
        cells = re.findall(r'<td>(.*?)</td>', row, re.DOTALL)
        cells = [c.strip() for c in cells if c.strip()]
        if not cells:
            continue
        if len(cells) >= 3:
            num, title, pages = cells[0], cells[1], cells[2]
            if num:
                lines.append(f"**{num}.** {title} — பக்கம் {pages}")
            else:
                lines.append(f"   - {title} — பக்கம் {pages}")
        elif len(cells) == 2:
            lines.append(f"- {cells[0]}: {cells[1]}")
        else:
            lines.append(f"- {cells[0]}")
    return "\n".join(lines) + "\n"

text = re.sub(r'<table[^>]*>.*?</table>', html_table_to_md, text, flags=re.DOTALL | re.IGNORECASE)
# Remove any leftover HTML tags
text = re.sub(r'<[^>]+>', '', text)

# ── 3. Clean OCR corruption: stray commas/punctuation inside Tamil words ──
# Patterns like அஷ்டாத,ர → அஷ்டாதர, க,தி → கதி, விபூ,தி → விபூதி etc.
# Rule: a Tamil character, then ,/₂/₃/₃ (subscript digits), then Tamil char
#        → remove the stray character between them
def fix_ocr_corruption(t):
    # Stray comma between Tamil letters (OCR artifact)
    t = re.sub(r'([஀-௿]),\s*([஀-௿])', r'\1\2', t)
    # Subscript digits used as OCR artifacts: ₂ ₃ ₄
    t = re.sub(r'([஀-௿])[₂₃₄]([஀-௿])', r'\1\2', t)
    # ₂/₃ at end of Tamil word
    t = re.sub(r'([஀-௿])[₂₃₄](\s)', r'\1\2', t)
    # Stray comma at start of Tamil word in middle of sentence
    t = re.sub(r'\s,\s*([஀-௿])', r' \1', t)
    return t

text = fix_ocr_corruption(text)

# ── 4. Convert page running-header lines → ## பக்கம்-N markers ──────────────
# These are OCR running headers printed at the top of each physical page:
#   "6 அஷ்டாதரஹஸ்யம்"  or  "104 அஷ்டாதரஹஸ்யம்"  (number then title)
#   "தத்வத்ரயம் 31"                                (title then number)
# We convert "N TitleText" → "## பக்கம்-N" so make_html2.py renders them
# as a small grey page-number badge instead of dropping them entirely.

# Matches both orderings:  "NN . BookTitle"  or  "BookTitle NN"
BOOK_TITLE_WORDS = (
    r'அஷ்டாதர\s*ஹஸ்யம்|அஷ்டாதச\s*ரஹஸ்யம்|அஷ்டாத[சஸ]ர\s*ஹஸ்யம்'
    r'|முமுக்ஷுப்படி|தத்வத்ரயம்|ஸ்ரீவசந\s*பூஷணம்|அர்த்த,?பஞ்சகம்'
    r'|அர்ச்சிராதி|தத்வபோக,?ரம்|நவவிதஸம்பந்தம்|ஸாரஸங்க்ரஹம்'
    r'|ஸம்ஸாரஸாம்ராஜ்யம்|ப்ரமேயசேகரம்|ப்ரபந்தரித்ராணம்|யாத்ருச்சிகப்படி|பரந்தபடி'
)
# "NNN BookTitle" or "NNN . BookTitle"
HEADER_NUM_FIRST = re.compile(
    r'^(\d{1,3})\s*\.?\s*(?:' + BOOK_TITLE_WORDS + r')\s*$'
)
# "BookTitle NNN"
HEADER_TITLE_FIRST = re.compile(
    r'^(?:' + BOOK_TITLE_WORDS + r')\s+(\d{1,3})\s*$'
)

def convert_page_header(line):
    s = line.strip()
    m = HEADER_NUM_FIRST.match(s)
    if m:
        return f'## பக்கம்-{m.group(1)}'
    m = HEADER_TITLE_FIRST.match(s)
    if m:
        return f'## பக்கம்-{m.group(1)}'
    return line

lines = text.split("\n")
lines = [convert_page_header(l) for l in lines]
text = "\n".join(lines)

# ── 5. Remove Roman-numeral section-continuation headings ────────────────
# Lines like "## II", "## III", "## IV" ... "## XLII" that are page-break markers
text = re.sub(r'\n##\s+(?:I{1,3}|IV|V?I{0,3}|IX|X{0,3}(?:IX|IV|V?I{0,3}))\s*\n',
              '\n', text)

# ── 6. Join OCR-split paragraph lines ────────────────────────────────────
# Tamil text is split across lines mid-sentence. Strategy:
# - A line ending with a Tamil letter (no punctuation) that is NOT a heading
#   should be joined to the next line IF the next line also starts with Tamil
#   and is not a heading/blank/HR.
def join_wrapped_lines(text):
    lines = text.split("\n")
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip()

        # Pass headings, blank lines, HR, blockquotes through unchanged
        if (not stripped
                or stripped.startswith("#")
                or stripped.startswith("---")
                or stripped.startswith(">")
                or stripped.startswith("**")
                or stripped.startswith("*அஷ்")
                or stripped.startswith("![")
                or stripped.startswith("|")):
            result.append(line)
            i += 1
            continue

        # Check if this line ends mid-word (Tamil char, no sentence-ending punctuation)
        last_char = stripped[-1] if stripped else ""
        ends_mid_word = (
            last_char in "அஆஇஈஉஊஏஐஒஓஔகசடதநபமயரலவழளறனஞஜஷஸஹ"
            or "஀" <= last_char <= "௿"  # any Tamil codepoint
        ) and last_char not in "।॥.!?:;,)"
        # Don't join very short lines — these are names/addresses/labels
        if len(stripped) < 30:
            ends_mid_word = False

        # Look ahead: if next line starts with Tamil and current ends mid-word → join
        if ends_mid_word and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if (next_line
                    and not next_line.startswith("#")
                    and not next_line.startswith("---")
                    and not next_line.startswith(">")
                    and not next_line.startswith("*")
                    and ("஀" <= next_line[0] <= "௿" or next_line[0].isdigit())):
                # Join: append next line content to current with space
                result.append(stripped + " " + next_line)
                i += 2
                continue

        result.append(line)
        i += 1
    return "\n".join(result)

# Run multiple passes to catch chains
for _ in range(6):
    prev = text
    text = join_wrapped_lines(text)
    if text == prev:
        break

# ── 7. Clean up footnote reference lines ─────────────────────────────────
# Lines like "##### a பெரியதிரு..." → convert to blockquote footnote
def footnote_to_blockquote(m):
    content = m.group(1).strip()
    return f"\n> *குறிப்பு: {content}*\n"

text = re.sub(r'#{3,6}\s+((?:[a-z]\s+.+))', footnote_to_blockquote, text)

# ── 8. Remove duplicate consecutive lines ────────────────────────────────
lines = text.split("\n")
deduped = []
prev = None
for line in lines:
    stripped = line.strip()
    if stripped and stripped == prev:
        continue  # skip exact duplicate
    deduped.append(line)
    if stripped:
        prev = stripped
    else:
        prev = None
text = "\n".join(deduped)

# ── 9. Collapse excessive blank lines (max 2 consecutive) ─────────────────
text = re.sub(r'\n{4,}', '\n\n\n', text)

# ── 10. Fix image references ──────────────────────────────────────────────
# Remove leftover "![alt text](image.png)" that have no real image
text = re.sub(r'!\[alt text\]\(image\.png\)', '', text)

# ── 11. Re-format numbered sūtra paragraphs ───────────────────────────────
# Paragraphs that start with "N." (where N is 1–3 digit number) inside body sections
# These should remain as paragraphs but without extra line breaks between them
# when they're part of the same section. We keep them as-is but ensure spacing.

# ── 12. Final structure cleanup ───────────────────────────────────────────
# Ensure every ## heading has a blank line before it
text = re.sub(r'([^\n])\n(#{1,6}\s)', r'\1\n\n\2', text)
# Ensure every ## heading has a blank line after it
text = re.sub(r'(#{1,6}[^\n]+)\n([^\n#])', r'\1\n\n\2', text)

# ── 13. Fix common OCR word-breaks: known bad patterns ───────────────────
replacements = [
    # Book title corruption
    (r'அஷ்டாத,\s*ஸ\s+ரஹஸ்யம்',  'அஷ்டாதச ரஹஸ்யம்'),
    (r'அஷ்டாத,\s*ர\s+ரஹஸ்யம்',  'அஷ்டாதச ரஹஸ்யம்'),
    (r'அஷ்டாத₃ர',                'அஷ்டாதச'),
    (r'அஷ்டாத,ர',                'அஷ்டாதச'),
    # Common corruption patterns
    (r'விபூ,தி',                  'விபூதி'),
    (r'அர்த்த,',                  'அர்த்த'),
    (r'தத்வபோக,ர',               'தத்வபோகர'),
    (r'ப்ரமேயபோக,ர',             'ப்ரமேயபோகர'),
    (r'அர்த்த,பஞ்சகம்',          'அர்த்தபஞ்சகம்'),
    (r'அர்ச்சிராதி,',            'அர்ச்சிராதி'),
    (r'ஸம்ஸாரமாகிற',             'ஸம்ஸாரமாகிற'),
    # Stray subscript digits
    (r'₂', ''),
    (r'₃', ''),
    (r'₄', ''),
]
for pattern, replacement in replacements:
    text = re.sub(pattern, replacement, text)

# Second pass of comma-between-Tamil-chars cleanup (now that we joined lines)
text = fix_ocr_corruption(text)

# ── 14. Add book metadata header ─────────────────────────────────────────
header = """# அஷ்டாதச ரஹஸ்யம்

**ஆசிரியர்:** பிள்ளைலோகாசார்யர்
**பதிப்பாசிரியர்:** ஸ்ரீ உ.வே. S. கிருஷ்ணஸ்வாமி அய்யங்கார் ஸ்வாமி
**வெளியீடு:** க்ரந்த பரிபாலந ட்ரஸ்ட், புத்தூர், திருச்சி

---

"""

# Remove the existing first heading if it's the title
text = re.sub(r'^#\s+அஷ்டாதச ரஹஸ்யம்\s*\n', '', text)
text = header + text.lstrip()

# ── 15. Write output ──────────────────────────────────────────────────────
with open(OUT, "w", encoding="utf-8") as f:
    f.write(text)

out_chars = len(text)
out_lines = text.count("\n")
print(f"  Output: {out_chars:,} chars, {out_lines:,} lines")
print(f"\nDone -> {OUT}")
