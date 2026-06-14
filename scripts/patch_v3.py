"""
patch_v3.py — Apply targeted fixes to formatted_v3.md in-place.
Does NOT re-run the full cleanup pipeline; only touches specific patterns.
"""
import re, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "sarvam_output", "astathasa_rahasyam_formatted_v3.md")

with open(PATH, encoding="utf-8") as f:
    text = f.read()

lines_before = text.count('\n')
print(f"Input: {len(text):,} chars, {lines_before:,} lines")

# ── Fix 1: Remove running page-headers that slipped through ──────────────────
# Patterns: "ஸ்ரீவசவூஷணம் 53", "ஸ்ரீவசநூஷணம் 55", "ஸ்ரீவசநூ,,ஷணம் 89" etc.
STRAY_HEADER = re.compile(
    r'^ஸ்ரீவச(?:[வந][ூு],*|ப[ூு])ஷணம்\s*\d*\s*$',
    re.MULTILINE | re.UNICODE
)
removed_headers = len(STRAY_HEADER.findall(text))
text = STRAY_HEADER.sub('', text)
print(f"Fix 1 – removed {removed_headers} stray running headers")

# ── Fix 2: Remove orphan sutra-number lines ("1. " / "2. " etc alone) ────────
ORPHAN_NUM = re.compile(r'^\d{1,3}\.\s*$', re.MULTILINE)
removed_orphans = len(ORPHAN_NUM.findall(text))
text = ORPHAN_NUM.sub('', text)
print(f"Fix 2 – removed {removed_orphans} orphan number lines")

# ── Fix 3: Convert bold-only lines to ## headings ────────────────────────────
# **Some Tamil heading text** → ## Some Tamil heading text
BOLD_HEADING = re.compile(r'^\*\*([^*\n]{10,})\*\*\s*$', re.MULTILINE)
upgraded_bold = len(BOLD_HEADING.findall(text))
text = BOLD_HEADING.sub(lambda m: f'## {m.group(1).strip()}', text)
print(f"Fix 3 – upgraded {upgraded_bold} bold lines to ## headings")

# ── Fix 4: Promote specific sub-section heading lines to ## headings ──────────
# "5. (iii) உபயஸாதாரண வைபவம்" → "## (iii) உபயஸாதாரண வைபவம்"
# "10. (i) புருஷகார வைபவம்" → "## (i) புருஷகார வைபவம்"
# Guards: must end with வைபவம் / ப்ரகரணம் / வைபவஞ்ச style words (section titles),
# not "பக்கம் ப்ரமாணம் காண்க" (page refs) or verse fragments.
SECTION_LABEL = re.compile(
    r'^(?:\d{1,3}\.\s+)?\((?:[ivxlcdmIVXLCDM]+)\)\s+[஀-௿][^\n]{5,60}(?:வைபவம்|ப்ரகரணம்|வைபவஞ்ச|ஸங்க்ரஹம்|நிஷ்டை|உபோத்காதம்|ஸ்வரூபம்)\s*$',
    re.MULTILINE | re.UNICODE
)

def _promote_section(m):
    s = m.group(0)
    s = re.sub(r'^\d{1,3}\.\s+', '', s)
    return f'## {s}'

promoted = len(SECTION_LABEL.findall(text))
text = SECTION_LABEL.sub(_promote_section, text)
print(f"Fix 4 – promoted {promoted} section labels to ## headings")

# ── Fix 5: Collapse runs of blank lines to max 1 ─────────────────────────────
text = re.sub(r'\n{3,}', '\n\n', text)

lines_after = text.count('\n')
print(f"Output: {len(text):,} chars, {lines_after:,} lines")

with open(PATH, 'w', encoding='utf-8') as f:
    f.write(text)

print(f"Done: {PATH}")
