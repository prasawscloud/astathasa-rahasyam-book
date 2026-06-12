"""
Convert astathasa_rahasyam_formatted.md → polished self-contained HTML book.
UX: sticky sidebar TOC, live Tamil search, scroll-spy, 3 themes, font-size controls.
"""
import re, html as htmllib, os, sys

import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
SRC = _os.path.join(_ROOT, "sarvam_output", "astathasa_rahasyam_formatted_v2.md")
OUT = _os.path.join(_ROOT, "docs", "index.html")

sys.stdout.reconfigure(encoding="utf-8")

print("Reading…")
with open(SRC, encoding="utf-8-sig") as f:  # utf-8-sig strips BOM if present
    raw = f.read()
print(f"  {len(raw):,} chars")

# ── Helpers ─────────────────────────────────────────────────────────────────
_seen = {}
def slugify(t):
    s = re.sub(r'[^\w஀-௿]', '-', t.strip())
    s = re.sub(r'-+', '-', s).strip('-').lower() or 'sec'
    n = _seen.get(s, 0); _seen[s] = n + 1
    return s if n == 0 else f'{s}-{n}'

def esc(t): return htmllib.escape(t, quote=False)

def inline(t):
    t = esc(t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<em>\1</em>', t)
    return t

# Cross-reference map: Tamil text → anchor slug
# Populated after headings are discovered; used in xref_body()
_XREFS = [
    # 18 Rahasyam works
    ('முமுக்ஷுப்படி',   '1-முமுக்ஷுப்படி'),
    ('தத்வத்ரயம்',      '2-தத்வத்ரயம்'),
    ('அர்த்தபஞ்சகம்',   '3-அர்த்தபஞ்சகம்'),
    ('ஸ்ரீவசநபூஷணம்',  '4-ஸ்ரீவசநபூஷணம்'),
    ('அர்ச்சிராதிதனியன்','5-அர்ச்சிராதிதனியன்'),
    ('ப்ரமேயசேகரம்',   '6-ப்ரமேயசேகரம்'),
    ('ப்ரபந்தரித்ராணம்','7-ப்ரபந்தரித்ராணம்'),
    ('ஸாரஸங்க்ரஹம்',   '8-ஸாரஸங்க்ரஹம்'),
    ('ஸம்ஸாரஸாம்ராஜ்யம்','19-ஸம்ஸாரஸாம்ராஜ்யம்'),
    ('நவவிதஸம்பந்தம்', '11-நவவிதஸம்பந்தம்'),
    ('யாத்ருச்சிகப்படி','2-யாத்ருச்சிகப்படி'),
    ('பரந்தபடி',        '13-பரந்தபடி'),
    # Key sub-sections
    ('திருமந்த்ரப்ரகரணம்','திருமந்த்ரப்ரகரணம்'),
    ('த்வயப்ரகரணம்',    'த்வயப்ரகரணம்-2'),
    ('சரமச்லோகப்ரகரணம்','சரமச்லோகப்ரகரணம்-3'),
]
# Build a single regex that matches any of the above Tamil phrases
_XREF_RE = re.compile('(' + '|'.join(re.escape(k) for k, _ in _XREFS) + ')')
_XREF_MAP = {k: v for k, v in _XREFS}

def xref_body(html_fragment):
    """Wrap known chapter/section names in <a class=xref> links, skipping text already inside a tag."""
    # Only process text nodes (between > and <)
    def replace_xrefs(m):
        word = m.group(0)
        slug = _XREF_MAP.get(word, '')
        if slug:
            return f'<a class="xref" href="#{slug}">{word}</a>'
        return word
    # Split on tags, only replace in text segments
    parts = re.split(r'(<[^>]+>)', html_fragment)
    result = []
    for part in parts:
        if part.startswith('<'):
            result.append(part)
        else:
            result.append(_XREF_RE.sub(replace_xrefs, part))
    return ''.join(result)

# ── Pre-clean ────────────────────────────────────────────────────────────────
# Convert "## பக்கம்-NNN" markers → inline page-badge HTML fragment
# Use a sentinel prefix so the main parser emits them as-is
raw = re.sub(
    r'^## பக்கம்-(\d+)\s*$',
    lambda m: f'__PAGEBADGE_{m.group(1)}__',
    raw, flags=re.MULTILINE
)

# ── Heading classification ────────────────────────────────────────────────────
SKIP_RE = re.compile(
    r'^(\d+\s*$|ஸ ஏஷ|ஆக அகார|ஹரவு|விஸ்வம்|ஜராம|தே தம்|அஸ்மாந்|'
    r'ப்ரஹ்மா உவாச|பகவாநுவாச|அஹமபி|பவந்தம்|1\.\s|2\.\s|3\.\s)'
)
def real_heading(s): return len(s) > 2 and not SKIP_RE.match(s.strip())

# ── TOC entry helpers ────────────────────────────────────────────────────────
# Matches page ranges like: 1—23  1-23  140-229  230 - 253  253--300  135—136  137
_PG_RANGE_RE = re.compile(r'([\d]+\s*[-—–]+\s*[\d]+|[\d]+)\s*$')

def _pg_link(pg_str):
    """Wrap a page range string in anchor links to #pg-N for the first page."""
    pg_str = pg_str.strip()
    m = re.match(r'^(\d+)', pg_str.replace('—','-').replace('–','-'))
    first = m.group(1) if m else None
    href = f'#pg-{first}' if first else '#'
    return f'<a class="toc-pg" href="{href}">{esc(pg_str)}</a>'

def _render_toc_row(num, title_html, pg_str, indent=False):
    pg = _pg_link(pg_str) if pg_str else ''
    ind_cls = ' toc-sub' if indent else ''
    num_html = f'<span class="toc-n">{esc(num)}.</span> ' if num else ''
    return (f'<div class="toc-row{ind_cls}">'
            f'<span class="toc-title">{num_html}{title_html}</span>'
            f'<span class="toc-dots"></span>'
            f'<span class="toc-pg-cell">{pg}</span>'
            f'</div>')

# Pattern: "**N.** Title — பக்கம் X—Y"  OR  "**N.** Title: X-Y"
_TOC_BOLD = re.compile(
    r'^\*\*(\d{1,2})\.\*\*\s+(.+?)\s*(?:[—\-–]+\s*பக்கம்\s*|:)\s*(.+)$'
)
# Pattern: "N Title X-Y"  (Format B, plain, used after second --- in TOC)
_TOC_PLAIN = re.compile(
    r'^(\d{1,2})\s+([^\d].+?)\s+([\d][\d\s\-—–]+[\d]|[\d]+)\s*$'
)
# Sub-item: "- (i) text: page-range"  or  "(i) text page-range"
_TOC_SUB = re.compile(
    r'^[-\s]*\(([ivxlIVXL]+)\)\s+(.+?):?\s+([\d][\d\s\-—–]+[\d]|[\d]+)\s*$'
)

_in_toc = [False]        # track whether we're inside the TOC section
_after_cover = [False]   # non-blank lines after the book cover h1 → book-meta
_in_colophon = [False]   # inside the ஆசார்யாக்ரேஸரரான dedication block

# ── Index / names-index entry detection ──────────────────────────────────────
# Pattern A: "N text ... page_num"  (no dot after N, space-sep, ends with digit/range)
#   e.g. "1 தர்மதர்மி ஜ்ஞாநபேதம் 27"   "11 திருவின் பெருமை 108 109"
IDX_NO_DOT = re.compile(r'^(\d{1,3})\s+(.+?)\s+([\d][\d\s,\-–—xivIV]*)$')

# Pattern B: "N. name (pages)"  — dot after number, possibly crammed entries on same line
#   e.g. "2. வேதம் 3. த்ரௌபதீ (53, 54) 4. பகவத்"
IDX_DOT    = re.compile(r'^\d{1,3}\.\s')

# Detect if a line has MULTIPLE crammed index entries: "22. ... 23. ... 35. ..."
MULTI_IDX  = re.compile(r'\d{1,3}\.\s+[^\d].*\d{1,3}\.\s')

def split_crammed_index(s):
    """Split '22. text1 23. text2 35. text3' into individual entry strings."""
    parts = re.split(r'(?=\b\d{1,3}\.\s)', s)
    return [p.strip() for p in parts if p.strip()]

# Detect "N text page" index line (no dot) — only valid in index context
# We'll track whether we are inside a known index section
_in_index = [False]

def is_index_nodot(s):
    """True if line looks like a numbered index entry without dot."""
    m = IDX_NO_DOT.match(s)
    if not m: return False
    # Must have Tamil text in the middle part
    mid = m.group(2)
    return any('஀' <= c <= '௿' for c in mid)

# ── Parse lines → HTML body + TOC ─────────────────────────────────────────────
toc = []       # (level, text, id)
out = []       # html fragments

lines = raw.split('\n')
N = len(lines)
i = 0

while i < N:
    line = lines[i]
    s = line.strip()
    i += 1

    # blank
    if not s:
        continue

    # Page badge sentinel  __PAGEBADGE_NNN__
    pb_m = re.match(r'^__PAGEBADGE_(\d+)__$', s)
    if pb_m:
        out.append(f'<div class="page-badge" id="pg-{pb_m.group(1)}"><span>பக்கம் {pb_m.group(1)}</span></div>')
        continue

    if re.match(r'^-{3,}$', s):
        out.append('<div class="divider"><span>❧ ॐ ❧</span></div>')
        continue

    # ::: fences — card box or centered block
    if s == ':::card':
        out.append('<div class="cover-card">')
        continue
    if s == ':::center':
        out.append('<div class="text-center">')
        continue
    if s == ':::highlight':
        out.append('<div class="highlight-block">')
        continue
    if s == ':::':
        out.append('</div>')
        continue

    # Heading — also resets toc context


    # Heading
    m = re.match(r'^(#{1,4})\s+(.*)', s)
    if m:
        lvl = len(m.group(1))
        txt = m.group(2).strip()
        sid = slugify(txt)
        # Track section context
        if 'ஸூசிகை' in txt or 'நாமங்கள்' in txt or 'பெயரகராதி' in txt:
            _in_index[0] = True
        elif lvl <= 2 and 'ஸூசிகை' not in txt:
            _in_index[0] = False
        if lvl <= 2:
            _in_toc[0] = False
        if 'ஆசார்யாக்ரேஸரரான' in txt:
            _after_cover[0] = False
        elif lvl <= 2:
            _in_colophon[0] = False
        if real_heading(txt):
            tag = f'h{min(lvl+1, 4)}'
            if lvl == 1: tag = 'h1'
            css = {1:'book-title',2:'chapter-heading',3:'section-heading',4:'subsec-heading'}.get(lvl,'section-heading')
            out.append(f'<{tag} id="{sid}" class="{css}">{inline(txt)}</{tag}>')
            # Flag: the paragraph immediately after the first h1 is book meta
            if lvl == 1 and not _after_cover[0] and len(out) <= 4:
                _after_cover[0] = True
            if lvl in (1,2,3):
                toc.append((lvl, txt, sid))
        else:
            out.append(f'<p class="page-ref">{inline(txt)}</p>')
        continue

    # Blockquote
    if s.startswith('>'):
        content = re.sub(r'^>\s*', '', s)
        out.append(f'<blockquote class="footnote">{xref_body(inline(content))}</blockquote>')
        continue

    # Image → ornament
    if s.startswith('!['):
        img_m = re.match(r'!\[([^\]]*)\]\(([^)]*)\)', s)
        if img_m and img_m.group(2).strip():
            alt_txt = esc(img_m.group(1))
            src = esc(img_m.group(2).strip())
            out.append(f'<figure class="book-figure"><img src="{src}" alt="{alt_txt}" loading="lazy"><figcaption>{alt_txt}</figcaption></figure>')
        else:
            out.append('<div class="img-ornament">✦</div>')
        continue

    # Bullet list (- or *) — but check for TOC sub-items first
    if re.match(r'^[-*]\s', s):
        # If in TOC context and line is a sub-item like "- (i) text: pages", render as toc-sub
        if _in_toc[0]:
            stripped = re.sub(r'^[-*]\s+', '', s)
            m_sub = _TOC_SUB.match(stripped)
            if m_sub:
                label = f'({m_sub.group(1)}) {xref_body(inline(m_sub.group(2)))}'
                out.append(_render_toc_row('', label, m_sub.group(3), indent=True))
                continue
        items = []
        j = i - 1
        while j < N and re.match(r'^[-*]\s', lines[j].strip()):
            items.append(re.sub(r'^[-*]\s+', '', lines[j].strip()))
            j += 1
        i = j
        out.append('<ul class="content-list">' +
                   ''.join(f'<li>{xref_body(inline(x))}</li>' for x in items) +
                   '</ul>')
        continue

    # ── Index entries (dot form): only inside known index sections ──────────
    if _in_index[0] and IDX_DOT.match(s):
        if MULTI_IDX.search(s):
            entries = split_crammed_index(s)
        else:
            entries = [s]
        rows = []
        for entry in entries:
            em = re.match(r'^(\d{1,3})\.\s+(.*)', entry)
            if em:
                rows.append(f'<tr><td class="idx-num">{esc(em.group(1))}.</td>'
                            f'<td class="idx-body">{inline(em.group(2))}</td></tr>')
        if rows:
            out.append('<table class="idx-table">' + ''.join(rows) + '</table>')
            continue

    # ── TOC Format B: "N Title X-Y"  (plain, no dot — must check before index) ──
    if not _in_index[0]:
        m_tp = _TOC_PLAIN.match(s)
        if m_tp and any('஀' <= c <= '௿' for c in m_tp.group(2)):
            _in_toc[0] = True
            out.append(_render_toc_row(m_tp.group(1), xref_body(inline(m_tp.group(2))), m_tp.group(3)))
            continue

    # ── TOC sub-item: "(i) text page-range" ─────────────────────────────────
    if _in_toc[0]:
        m_sub = _TOC_SUB.match(s)
        if m_sub:
            label = f'({m_sub.group(1)}) {xref_body(inline(m_sub.group(2)))}'
            out.append(_render_toc_row('', label, m_sub.group(3), indent=True))
            continue

    # ── Index entries (no-dot form): "N text pages" ─────────────────────────
    if _in_index[0] and is_index_nodot(s):
        # Collect consecutive no-dot index lines
        rows = []
        cur = s
        while cur:
            m2 = IDX_NO_DOT.match(cur)
            if m2:
                body_txt = m2.group(2)
                pg_txt = m2.group(3).strip()
                search_q = body_txt[:40].replace('"', '&quot;')
                pg_cell = f'<a href="#" data-search="{search_q}">{esc(pg_txt)}</a>'
                rows.append(f'<tr><td class="idx-num">{esc(m2.group(1))}.</td>'
                            f'<td class="idx-body">{inline(body_txt)}</td>'
                            f'<td class="idx-pg">{pg_cell}</td></tr>')
            cur = None
            if i < N and is_index_nodot(lines[i].strip()):
                cur = lines[i].strip()
                i += 1
        out.append('<table class="idx-table">' + ''.join(rows) + '</table>')
        continue

    # ── Numbered sūtra: starts with digit(s) then dot/space + Tamil text ────
    # Distinguish sūtras (philosophical text) from index by context:
    # sūtras have Tamil body text starting right after the number
    if re.match(r'^\d{1,3}[\.\s]', s):
        m2 = re.match(r'^(\d{1,3})[\.\s]\s*(.*)', s)
        if m2:
            num, body = m2.group(1), m2.group(2)
            # If body has Tamil content (not just page numbers), treat as sūtra
            has_tamil = any('஀' <= c <= '௿' for c in body)
            if has_tamil:
                out.append(f'<p class="sutra"><span class="sutra-num">{esc(num)}.</span> {inline(body)}</p>')
                continue

    # ── TOC Format A: "**N.** Title — பக்கம் X—Y" ──────────────────────────
    if re.match(r'^\*\*\d', s):
        m_toc = _TOC_BOLD.match(s)
        if m_toc:
            _in_toc[0] = True
            out.append(_render_toc_row(m_toc.group(1), xref_body(inline(m_toc.group(2))), m_toc.group(3)))
        else:
            out.append(f'<p class="toc-entry">{xref_body(inline(s))}</p>')
        continue

    # Regular paragraph — collect continuation lines
    para = [s]
    while i < N:
        nx = lines[i].strip()
        if (not nx or nx.startswith('#') or re.match(r'^-{3,}$', nx)
                or nx.startswith('>') or nx.startswith('![')
                or nx.startswith(':::')
                or re.match(r'^[-*]\s', nx)
                or re.match(r'^\*\*\d', nx)
                or (_in_index[0] and IDX_DOT.match(nx))
                or (_in_index[0] and is_index_nodot(nx))):
            break
        para.append(nx)
        i += 1
    out.append(f'<p>{xref_body(inline(" ".join(para)))}</p>')

body_html = '\n'.join(out)
print(f"  Body fragments: {len(out)}")
print(f"  TOC entries: {len(toc)}")

# ── Build TOC HTML ─────────────────────────────────────────────────────────────
# Classify l2 entries: "chapter" = starts with digit+dot (1. முமுக்ஷுப்படி)
#                      "section" = everything else under a chapter
_CHAPTER_RE = re.compile(r'^\d{1,2}\.\s')

toc_items = []
_cur_chapter_depth = [0]   # track whether we're inside a chapter group

for lvl, txt, sid in toc:
    if lvl == 1:
        cls = 'toc-l1'
        _cur_chapter_depth[0] = 0
    elif lvl == 2:
        if _CHAPTER_RE.match(txt):
            cls = 'toc-l2 toc-chapter'
            _cur_chapter_depth[0] = 1
        elif _cur_chapter_depth[0]:
            cls = 'toc-l2 toc-section'
        else:
            cls = 'toc-l2'
    else:
        cls = f'toc-l{lvl}'

    toc_items.append(f'<li class="{cls}"><a href="#{sid}" data-id="{sid}">{esc(txt)}</a></li>')
toc_html = '\n'.join(toc_items)


# ── Full HTML ──────────────────────────────────────────────────────────────────
HTML = f"""<!DOCTYPE html>
<html lang="ta">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>அஷ்டாதச ரஹஸ்யம் — பிள்ளைலோகாசார்யர்</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+Tamil:wght@400;600;700&family=Noto+Sans+Tamil:wght@400;500&display=swap');
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}

:root{{
  --bg:#fdf6ec;--bg2:#f5ead6;--sb-bg:#2c1a0e;--sb-fg:#f0d9b5;--sb-acc:#e8a040;
  --tx:#1a0f05;--tx2:#6b4c2a;--acc:#8b1a1a;--acc2:#c9630a;--bdr:#d4b896;
  --sn:#8b1a1a;--card:#fffaf3;--shad:0 2px 12px rgba(0,0,0,.12);
  --fs:1.05rem;--lh:1.95;--sw:295px;--th:52px;
  --fn:'Noto Serif Tamil',serif;--fui:'Noto Sans Tamil',sans-serif
}}
[data-theme=dark]{{
  --bg:#12100e;--bg2:#1e1812;--sb-bg:#0d0b09;--sb-fg:#c9a96e;
  --tx:#e8d5b7;--tx2:#9e8060;--acc:#e05050;--acc2:#e88030;--bdr:#3a2e20;--sn:#e05050;--card:#1a1510
}}
[data-theme=sepia]{{
  --bg:#f0e6d0;--bg2:#e4d5b8;--sb-bg:#3d2b1f;--sb-fg:#f0d9b5;
  --tx:#2c1a08;--tx2:#7a5a3a;--acc:#7a1a1a;--bdr:#c8a878;--card:#f5ead6
}}

html{{scroll-behavior:smooth}}
body{{font-family:var(--fn);font-size:var(--fs);line-height:var(--lh);background:var(--bg);color:var(--tx);display:flex;flex-direction:column;min-height:100vh}}

/* TOP BAR */
#top{{position:fixed;top:0;left:0;right:0;z-index:200;height:var(--th);background:var(--sb-bg);color:var(--sb-fg);display:flex;align-items:center;gap:8px;padding:0 14px;box-shadow:0 2px 8px rgba(0,0,0,.35)}}
#mbtn{{background:none;border:none;color:var(--sb-acc);font-size:1.4rem;cursor:pointer;padding:5px 8px;border-radius:6px}}
#mbtn:hover{{background:rgba(255,255,255,.1)}}
#sw{{flex:1;max-width:500px;position:relative}}
#si{{width:100%;padding:6px 34px 6px 14px;border-radius:18px;border:1px solid rgba(255,255,255,.2);background:rgba(255,255,255,.1);color:var(--sb-fg);font-family:var(--fui);font-size:.88rem;outline:none}}
#si::placeholder{{color:rgba(255,255,255,.38)}}
#si:focus{{background:rgba(255,255,255,.17);border-color:var(--sb-acc)}}
#scl{{position:absolute;right:9px;top:50%;transform:translateY(-50%);background:none;border:none;color:var(--sb-acc);cursor:pointer;font-size:.95rem;display:none}}
#snav{{display:flex;align-items:center;gap:3px;flex-shrink:0;font-size:.8rem}}
#scnt{{color:var(--sb-acc);font-weight:700;min-width:44px}}
.snb{{background:none;border:1px solid rgba(255,255,255,.22);border-radius:4px;color:var(--sb-fg);padding:2px 7px;cursor:pointer;font-size:.85rem}}
.snb:hover{{background:rgba(255,255,255,.14)}}
#ctrls{{display:flex;align-items:center;gap:6px;flex-shrink:0}}
.cb{{background:none;border:1px solid rgba(255,255,255,.2);border-radius:5px;color:var(--sb-fg);padding:3px 9px;cursor:pointer;font-size:.8rem;font-family:var(--fui);white-space:nowrap}}
.cb:hover{{background:rgba(255,255,255,.12)}}

/* SIDEBAR */
#toc{{position:fixed;top:var(--th);left:0;bottom:0;width:var(--sw);z-index:150;background:var(--sb-bg);display:flex;flex-direction:column;transition:transform .28s ease;border-right:1px solid rgba(255,255,255,.06)}}
#toc.hide{{transform:translateX(calc(-1*var(--sw)))}}
.th{{display:flex;align-items:center;justify-content:space-between;padding:13px 15px 9px;border-bottom:1px solid rgba(255,255,255,.09);flex-shrink:0}}
.tt{{font-family:var(--fui);font-size:.92rem;font-weight:700;color:var(--sb-acc);letter-spacing:.05em}}
#tc{{background:none;border:none;color:var(--sb-fg);cursor:pointer;font-size:1rem;opacity:.55}}
#tc:hover{{opacity:1}}
.ts{{padding:9px 11px;flex-shrink:0}}
#tf{{width:100%;padding:5px 11px;border-radius:13px;border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.07);color:var(--sb-fg);font-family:var(--fui);font-size:.8rem;outline:none}}
#tf::placeholder{{color:rgba(255,255,255,.32)}}
#tf:focus{{border-color:var(--sb-acc)}}
#tl{{flex:1;overflow-y:auto;list-style:none;padding:3px 0 24px;scrollbar-width:thin;scrollbar-color:rgba(255,255,255,.13) transparent}}
#tl::-webkit-scrollbar{{width:4px}}
#tl::-webkit-scrollbar-thumb{{background:rgba(255,255,255,.13);border-radius:2px}}
#tl li a{{display:block;padding:5px 14px;color:var(--sb-fg);text-decoration:none;font-family:var(--fui);font-size:.82rem;line-height:1.35;transition:background .13s,color .13s;border-left:3px solid transparent}}
#tl li a:hover{{background:rgba(255,255,255,.07);color:var(--sb-acc)}}
#tl li.active a{{border-left-color:var(--sb-acc);color:var(--sb-acc);background:rgba(232,160,64,.1)}}

/* L1 — book / top-level titles */
#tl li.toc-l1 a{{font-size:.86rem;font-weight:700;padding-left:12px;color:var(--sb-acc);text-transform:uppercase;letter-spacing:.04em;margin-top:4px}}

/* L2 chapter entries  e.g. "1. முமுக்ஷுப்படி" */
#tl li.toc-chapter{{margin-top:6px}}
#tl li.toc-chapter a{{font-size:.84rem;font-weight:700;padding-left:14px;color:var(--sb-fg)}}

/* L2 section entries — sub-items under a chapter, indented with guide line */
#tl li.toc-section a{{
  padding-left:26px;
  font-size:.79rem;
  font-weight:400;
  opacity:.82;
  border-left:3px solid transparent;
  position:relative;
}}
#tl li.toc-section a::before{{
  content:'';
  position:absolute;
  left:14px;
  top:0;bottom:0;
  width:1px;
  background:rgba(255,255,255,.12);
}}
#tl li.toc-section.active a::before{{background:var(--sb-acc);opacity:.5}}

/* L2 generic (not chapter/section classified) */
#tl li.toc-l2:not(.toc-chapter):not(.toc-section) a{{font-weight:600;padding-left:14px}}

/* L3 — deepest level */
#tl li.toc-l3 a{{padding-left:36px;font-size:.76rem;opacity:.75}}

#tl li.hid{{display:none}}

/* MAIN */
#main{{margin-top:var(--th);margin-left:var(--sw);transition:margin-left .28s ease;min-height:calc(100vh - var(--th))}}
#main.wide{{margin-left:0}}
#ct{{max-width:820px;margin:0 auto;padding:44px 38px 100px}}

/* TYPOGRAPHY */

/* ── Book cover card ────────────────────────────────────── */
h1.book-title{{
  font-size:3rem;
  font-weight:700;
  color:var(--acc);
  text-align:center;
  margin:0;
  letter-spacing:.06em;
  line-height:1.2;
}}
/* Cover card — unified box containing title + meta lines */
div.cover-card{{
  background:linear-gradient(160deg,var(--bg2) 0%,var(--bg) 100%);
  border:2px solid var(--bdr);
  border-radius:12px;
  padding:2.4rem 2rem 1.4rem;
  margin:1.2rem 0 2rem;
  box-shadow:0 4px 24px rgba(0,0,0,.10);
  text-align:center;
}}
div.cover-card h1.book-title{{
  margin:0 0 1.2rem;
}}
div.cover-card h1.book-title::before,
div.cover-card h1.book-title::after{{
  content:'';
  display:block;
  height:2px;
  background:linear-gradient(90deg,transparent,var(--bdr),transparent);
  width:60%;
  margin:.8rem auto 0;
}}
div.cover-card h1.book-title::before{{
  margin:0 auto .8rem;
}}
div.book-meta-line{{
  display:block;
  padding:.28em 0;
  border-top:1px solid var(--bdr);
  font-family:var(--fui);font-size:.92rem;color:var(--tx2);
  text-align:center;
}}
div.book-meta-line strong{{color:var(--acc2);margin-right:.3em}}
/* Auspicious occasion sentence */
/* Centered block */
.text-center,.text-center p,.text-center h1,.text-center h2,.text-center h3,.text-center h4{{
  text-align:center;
}}
/* Highlight block — auspicious / special occasion text */
.highlight-block{{
  background:linear-gradient(135deg,rgba(180,120,40,.14) 0%,rgba(180,120,40,.05) 100%);
  border:2px solid var(--acc);
  border-radius:10px;
  padding:1rem 1.4rem;
  margin:1.2em 0;
  text-align:center;
  box-shadow:0 2px 12px rgba(180,120,40,.15);
}}
.highlight-block p{{
  font-family:'Noto Serif Tamil',Georgia,serif;
  font-size:1.05rem;
  font-weight:600;
  color:var(--acc);
  line-height:1.8;
  margin:0;
}}

/* ── Colophon card — publication dedication block ─── */
.colophon-card{{
  background:linear-gradient(160deg,var(--bg2) 0%,var(--bg) 100%);
  border:2px solid var(--bdr);
  border-radius:12px;
  padding:2rem 2.4rem;
  margin:2.4em 0;
  box-shadow:0 4px 24px rgba(0,0,0,.10);
  text-align:center;
  position:relative;
}}
.colophon-card::before{{
  content:'✦ ✦ ✦';
  display:block;
  text-align:center;
  color:var(--acc);
  font-size:.85rem;
  letter-spacing:.5em;
  margin-bottom:1.2em;
  opacity:.6;
}}
.colophon-card::after{{
  content:'✦ ✦ ✦';
  display:block;
  text-align:center;
  color:var(--acc);
  font-size:.85rem;
  letter-spacing:.5em;
  margin-top:1.2em;
  opacity:.6;
}}
.colophon-card h2.chapter-heading,
.colophon-card h3.section-heading,
.colophon-card h4.subsec-heading{{
  border-bottom:none;
  margin:.3em 0 .2em;
  font-size:1.25rem;
  text-align:center;
}}
p.colophon-p{{
  font-family:var(--fui);
  font-size:.95rem;
  color:var(--tx2);
  text-align:center;
  margin:.5em 0;
  line-height:1.75;
  hyphens:none;
}}
p.colophon-p strong{{color:var(--acc2)}}
h2.chapter-heading{{font-size:1.45rem;font-weight:700;color:var(--acc);margin:2.4em 0 .55em;padding-bottom:.28em;border-bottom:2px solid var(--bdr);scroll-margin-top:calc(var(--th) + 18px)}}
h3.section-heading{{font-size:1.15rem;font-weight:600;color:var(--acc2);margin:1.7em 0 .45em;scroll-margin-top:calc(var(--th) + 18px)}}
h4.subsec-heading{{font-size:1rem;font-weight:600;color:var(--tx2);margin:1.3em 0 .35em;scroll-margin-top:calc(var(--th) + 18px)}}

p{{margin:0 0 .75em;text-align:justify;hyphens:auto}}
p.toc-entry{{margin:.18em 0 .18em 1em;text-align:left;hyphens:none}}
p.toc-entry strong{{color:var(--sn);margin-right:.35em}}

/* TOC rows with dotted leader + right-aligned page link */
.toc-row{{display:flex;align-items:baseline;gap:4px;margin:.28em 0;line-height:1.5}}
.toc-row.toc-sub{{margin:.12em 0 .12em 1.8em;font-size:.9em;opacity:.88}}
.toc-n{{color:var(--sn);font-weight:700;flex-shrink:0;min-width:1.8em}}
.toc-title{{flex-shrink:0;max-width:72%}}
.toc-dots{{flex:1;border-bottom:1px dotted var(--bdr);margin:0 5px;min-width:12px;position:relative;top:-.2em}}
.toc-pg-cell{{flex-shrink:0;text-align:right;white-space:nowrap}}
a.toc-pg{{color:var(--acc2);text-decoration:none;font-family:var(--fui);font-size:.88em;font-weight:600;border-bottom:1px dotted var(--acc2);white-space:nowrap}}
a.toc-pg:hover{{color:var(--acc);border-bottom-style:solid}}
p.sutra{{display:flex;gap:.5em;align-items:baseline;margin:.3em 0}}
.sutra-num{{color:var(--sn);font-weight:700;font-size:.84em;flex-shrink:0;min-width:2.1em;text-align:right}}

blockquote.footnote{{border-left:3px solid var(--bdr);padding:3px 0 3px 13px;color:var(--tx2);font-size:.86rem;margin:.5em 0 .5em 1em;font-style:italic}}

.content-list{{list-style:none;padding:0;margin:.4em 0 .8em}}
.content-list li{{padding:2px 0 2px 17px;position:relative;font-size:.94rem}}
.content-list li::before{{content:'▸';position:absolute;left:0;color:var(--acc2)}}

.divider{{text-align:center;margin:1.8em 0;color:var(--bdr)}}
.divider span{{font-size:1rem;color:var(--acc);padding:0 .6em;background:var(--bg)}}
.divider::before{{content:'';display:block;border-top:1px solid var(--bdr);margin-bottom:-0.7em}}

.img-ornament{{text-align:center;color:var(--bdr);font-size:1.8rem;margin:1em 0;opacity:.45}}
figure.book-figure{{
  text-align:center;
  margin:1.6em auto 1.8em;
  max-width:680px;
}}
figure.book-figure img{{
  max-width:100%;height:auto;display:block;margin:0 auto;
  background:#1a0f05;
  border-radius:8px;
  padding:18px 24px;
  box-shadow:0 4px 18px rgba(0,0,0,.35);
}}
figure.book-figure figcaption{{
  font-family:var(--fui);font-size:.82rem;color:var(--tx2);
  margin-top:.55em;font-style:italic;letter-spacing:.04em;
  opacity:.8;
}}
.page-ref{{font-size:.8rem;color:var(--tx2);font-family:var(--fui);margin:.15em 0}}
p.meta{{font-family:var(--fui);font-size:.88rem;color:var(--tx2);text-align:center;margin:2px 0}}

/* PAGE BADGE — subtle marker at each physical page boundary */
.page-badge{{
  display:flex;align-items:center;gap:8px;
  margin:1.1em 0 .5em;
  opacity:.55;
  transition:opacity .2s;
}}
.page-badge:hover{{opacity:1}}
.page-badge::before,.page-badge::after{{
  content:'';flex:1;height:1px;background:var(--bdr);opacity:.5;
}}
.page-badge span{{
  font-family:var(--fui);font-size:.72rem;color:var(--tx2);
  white-space:nowrap;padding:1px 7px;
  border:1px solid var(--bdr);border-radius:10px;
  letter-spacing:.04em;
}}

/* INDEX TABLES */
table.idx-table{{
  border-collapse:collapse;
  width:100%;margin:.2em 0 .15em;
  font-family:var(--fui);font-size:.92rem;
}}
table.idx-table tr:hover td{{background:rgba(0,0,0,.03)}}
table.idx-table td{{
  padding:3px 6px 3px 2px;
  vertical-align:top;
  border-bottom:1px solid var(--bdr);
  line-height:1.5;
}}
td.idx-num{{
  color:var(--sn);font-weight:700;
  white-space:nowrap;width:2.4em;text-align:right;
  padding-right:8px;
}}
td.idx-body{{color:var(--tx)}}
td.idx-pg{{
  color:var(--tx2);white-space:nowrap;
  text-align:right;font-size:.82rem;padding-left:8px;
}}
td.idx-pg a{{color:var(--acc2);text-decoration:none;border-bottom:1px dotted var(--acc2)}}
td.idx-pg a:hover{{color:var(--acc);border-bottom-style:solid}}
a.xref{{color:var(--acc2);text-decoration:none;border-bottom:1px dotted var(--acc2)}}
a.xref:hover{{color:var(--acc);border-bottom-style:solid}}

/* HEADING FLASH (TOC click) */
@keyframes headFlash{{
  0%{{background:rgba(232,160,64,.55);box-shadow:0 0 0 4px rgba(232,160,64,.3)}}
  60%{{background:rgba(232,160,64,.22);box-shadow:0 0 0 2px rgba(232,160,64,.12)}}
  100%{{background:transparent;box-shadow:none}}
}}
.head-flash{{animation:headFlash 1.6s ease-out}}

/* SEARCH HIGHLIGHT */
mark.hl{{background:#ffe060;color:#1a0f05;border-radius:2px;padding:0 1px}}
mark.hl.cur{{background:#ff7b00;color:#fff;outline:2px solid #ff7b00}}

/* PROGRESS */
#pb-wrap{{position:fixed;top:var(--th);left:0;right:0;z-index:300;height:3px}}
#pb{{height:100%;background:var(--acc2);width:0%;transition:width .1s}}

/* BACK TOP */
#bt{{position:fixed;bottom:26px;right:22px;z-index:100;background:var(--acc);color:#fff;border:none;border-radius:50%;width:42px;height:42px;font-size:1.1rem;cursor:pointer;box-shadow:var(--shad);opacity:0;transition:opacity .3s;display:flex;align-items:center;justify-content:center}}
#bt.vis{{opacity:1}}
#bt:hover{{background:var(--acc2)}}

/* OVERLAY */
#ov{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:140}}

/* PRINT */
@media print{{
  #top,#toc,#pb-wrap,#bt,#ov{{display:none!important}}
  #main{{margin:0!important}}
  #ct{{max-width:100%;padding:20px}}
  h2.chapter-heading{{page-break-before:always}}
}}
/* MOBILE */
@media(max-width:680px){{
  :root{{--sw:275px}}
  #toc{{transform:translateX(calc(-1*var(--sw)))}}
  #toc.open{{transform:translateX(0)}}
  #main{{margin-left:0!important}}
  #ct{{padding:24px 16px 80px}}
  h1.book-title{{font-size:2rem}}
  div.cover-card{{padding:1.6rem 1.2rem 1.4rem;margin:.8rem 0 1.4rem}}
  #sw{{max-width:180px}}
}}
</style>
</head>
<body>
<div id="pb-wrap"><div id="pb"></div></div>

<header id="top">
  <button id="mbtn" title="உள்ளடக்கம்">☰</button>
  <div id="sw">
    <input id="si" type="search" placeholder="தமிழ் / English தேடு… (Ctrl+K)" autocomplete="off" spellcheck="false">
    <button id="scl" title="Clear">✕</button>
  </div>
  <div id="snav">
    <span id="scnt"></span>
    <button class="snb" id="sp">▲</button>
    <button class="snb" id="sn">▼</button>
  </div>
  <div id="ctrls">
    <button class="cb" id="fd">A−</button>
    <button class="cb" id="fi">A+</button>
    <button class="cb" id="tb">☀ கோட்பாடு</button>
    <button class="cb" onclick="window.print()">⎙</button>
  </div>
</header>

<nav id="toc">
  <div class="th">
    <span class="tt">உள்ளடக்கம்</span>
    <button id="tc">✕</button>
  </div>
  <div class="ts"><input id="tf" type="search" placeholder="தலைப்பு தேடு…" autocomplete="off"></div>
  <ul id="tl">
{toc_html}
  </ul>
</nav>

<div id="ov" onclick="hideToc()"></div>

<main id="main">
  <div id="ct">
{body_html}
  </div>
</main>

<button id="bt" title="மேலே">↑</button>

<script>
// Theme
const TH=['','sepia','dark'], TL=['☀ வெப்பம்','📜 செபியா','🌙 இரவு'];
let ti=+localStorage.getItem('ar-t')||0;
const tBtn=document.getElementById('tb');
function setT(n){{ti=((n%3)+3)%3;document.documentElement.dataset.theme=TH[ti];tBtn.textContent=TL[ti];localStorage.setItem('ar-t',ti)}}
tBtn.onclick=()=>setT(ti+1); setT(ti);

// Font size
let fs=+localStorage.getItem('ar-fs')||1.05;
const applyFs=()=>{{document.documentElement.style.setProperty('--fs',fs+'rem');localStorage.setItem('ar-fs',fs)}};
applyFs();
document.getElementById('fi').onclick=()=>{{fs=Math.min(1.5,fs+.08);applyFs()}};
document.getElementById('fd').onclick=()=>{{fs=Math.max(.82,fs-.08);applyFs()}};

// Sidebar
const toc=document.getElementById('toc'),main=document.getElementById('main'),ov=document.getElementById('ov');
let open=window.innerWidth>680;
function showToc(){{open=true;toc.classList.remove('hide');toc.classList.add('open');if(window.innerWidth>680)main.classList.remove('wide');else ov.style.display='block'}}
function hideToc(){{open=false;toc.classList.add('hide');toc.classList.remove('open');main.classList.add('wide');ov.style.display='none'}}
function togToc(){{open?hideToc():showToc()}}
document.getElementById('mbtn').onclick=togToc;
document.getElementById('tc').onclick=hideToc;
if(!open){{toc.classList.add('hide');main.classList.add('wide')}}
document.querySelectorAll('#tl a').forEach(a=>a.addEventListener('click',e=>{{
  if(window.innerWidth<=680)hideToc();
  const id=a.dataset.id;
  if(id){{
    const h=document.getElementById(id);
    if(h){{
      h.classList.remove('head-flash');
      void h.offsetWidth; // force reflow to restart animation
      h.classList.add('head-flash');
      h.addEventListener('animationend',()=>h.classList.remove('head-flash'),{{once:true}});
    }}
  }}
}}));

// TOC filter
document.getElementById('tf').addEventListener('input',function(){{
  const q=this.value.trim().toLowerCase();
  document.querySelectorAll('#tl li').forEach(li=>{{
    li.classList.toggle('hid',q.length>0&&!li.textContent.toLowerCase().includes(q))
  }})
}});

// Scroll spy
const heads=Array.from(document.querySelectorAll('h2[id],h3[id]'));
const lmap={{}};
document.querySelectorAll('#tl a[data-id]').forEach(a=>lmap[a.dataset.id]=a.parentElement);
let curId=null;
function spy(){{
  const top=window.scrollY+window.innerHeight*.22;
  let act=null;
  for(const h of heads){{if(h.offsetTop<=top)act=h.id;else break}}
  if(act===curId)return; curId=act;
  Object.values(lmap).forEach(li=>li.classList.remove('active'));
  if(act&&lmap[act]){{
    lmap[act].classList.add('active');
    const li=lmap[act],tl=document.getElementById('tl');
    const lt=li.offsetTop,lh=li.offsetHeight,tt=tl.scrollTop,th=tl.clientHeight;
    if(lt<tt||lt+lh>tt+th)tl.scrollTo({{top:lt-th/3,behavior:'smooth'}})
  }}
}}

// Progress
const pb=document.getElementById('pb');
function upPb(){{const tot=document.body.scrollHeight-window.innerHeight;pb.style.width=(tot>0?window.scrollY/tot*100:0)+'%'}}

// Back to top
const bt=document.getElementById('bt');
bt.onclick=()=>window.scrollTo({{top:0,behavior:'smooth'}});
window.addEventListener('scroll',()=>{{spy();upPb();bt.classList.toggle('vis',window.scrollY>400)}},{{passive:true}});

// Search
const si=document.getElementById('si'),scl=document.getElementById('scl'),scnt=document.getElementById('scnt');
const ct=document.getElementById('ct');
let origHtml=null,marks=[],cur=-1;

function clearSrch(){{
  if(origHtml!==null){{ct.innerHTML=origHtml;origHtml=null}}
  marks=[];cur=-1;scnt.textContent='';scl.style.display='none';
}}

function doSearch(q){{
  if(origHtml!==null)ct.innerHTML=origHtml; else origHtml=ct.innerHTML;
  q=q.trim();
  if(!q||q.length<2){{if(origHtml){{ct.innerHTML=origHtml;origHtml=null}}marks=[];cur=-1;scnt.textContent='';return}}
  const esc2=q.replace(/[.*+?^${{}}()|[\\]\\\\]/g,'\\\\$&');
  const re=new RegExp('('+esc2+')','gi');
  const walk=document.createTreeWalker(ct,NodeFilter.SHOW_TEXT,{{acceptNode(n){{
    const p=n.parentElement;
    return(!p||p.tagName==='SCRIPT'||p.tagName==='STYLE')?NodeFilter.FILTER_REJECT:NodeFilter.FILTER_ACCEPT
  }}}});
  const nodes=[];while(walk.nextNode())nodes.push(walk.currentNode);
  nodes.forEach(node=>{{
    if(!re.test(node.nodeValue))return; re.lastIndex=0;
    const f=document.createDocumentFragment();let last=0,m;
    while((m=re.exec(node.nodeValue))!==null){{
      if(m.index>last)f.appendChild(document.createTextNode(node.nodeValue.slice(last,m.index)));
      const mk=document.createElement('mark');mk.className='hl';mk.textContent=m[1];f.appendChild(mk);last=re.lastIndex
    }}
    if(last<node.nodeValue.length)f.appendChild(document.createTextNode(node.nodeValue.slice(last)));
    node.parentNode.replaceChild(f,node)
  }});
  marks=Array.from(ct.querySelectorAll('mark.hl'));cur=marks.length?0:-1;hlCur();
  scnt.textContent=marks.length?`${{cur+1}}/${{marks.length}}`:'0';
  scl.style.display=q?'block':'none';
}}

function hlCur(){{
  marks.forEach((m,i)=>m.classList.toggle('cur',i===cur));
  if(cur>=0&&marks[cur]){{marks[cur].scrollIntoView({{block:'center',behavior:'smooth'}});scnt.textContent=`${{cur+1}}/${{marks.length}}`}}
}}
function nxt(){{if(!marks.length)return;cur=(cur+1)%marks.length;hlCur()}}
function prv(){{if(!marks.length)return;cur=(cur-1+marks.length)%marks.length;hlCur()}}

let stimer=null;
si.addEventListener('input',()=>{{clearTimeout(stimer);stimer=setTimeout(()=>doSearch(si.value),260);scl.style.display=si.value?'block':'none'}});
si.addEventListener('keydown',e=>{{if(e.key==='Enter'){{e.preventDefault();e.shiftKey?prv():nxt()}}if(e.key==='Escape'){{clearSrch();si.value=''}}}});
document.getElementById('sp').onclick=prv;
document.getElementById('sn').onclick=nxt;
scl.onclick=()=>{{clearSrch();si.value=''}};
document.addEventListener('keydown',e=>{{if((e.ctrlKey||e.metaKey)&&e.key==='k'){{e.preventDefault();si.focus();si.select()}}}});

// Index page links — clicking td.idx-pg triggers search for the body text
document.querySelectorAll('td.idx-pg a[data-search]').forEach(a=>{{
  a.addEventListener('click',e=>{{
    e.preventDefault();
    const q=a.dataset.search;
    si.value=q;
    si.dispatchEvent(new Event('input'));
    // after search marks are placed, jump to first match
    setTimeout(()=>{{
      if(marks.length){{cur=0;hlCur()}}
    }},320);
  }});
}});

spy();upPb();
</script>
</body>
</html>"""

print("Writing HTML…")
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(HTML)

mb = os.path.getsize(OUT)/1024/1024
print(f"Done: {OUT}  ({mb:.2f} MB)")
