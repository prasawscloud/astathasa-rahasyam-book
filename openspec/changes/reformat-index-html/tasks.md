## 1. Setup

- [x] 1.1 Copy `docs/index.html` to `docs/index_v1.html` as the working file for all subsequent tasks (never edit `docs/index.html`)
- [x] 1.2 Re-run the href/id cross-reference scan and duplicate-paragraph scan against `docs/index_v1.html` to reconfirm baseline counts (45 broken `#pg-N`, 3 mislabeled xrefs, 1 mistemplated errata row, 187 placeholder strings)

## 2. Fix broken links (book-link-integrity)

- [x] 2.1 Build the page-number → chapter/section id map from the TOC's own text (each `toc-row`'s stated page range next to its heading id; used sidebar TOC `data-id` entries too since not every in-content row wraps its title in a link; used nearest-numeric-neighbor fallback for the 9 page numbers with no directly-matching row)
- [x] 2.2 Rewrite all 45 `href="#pg-N"` links to the mapped chapter/sub-section id
- [x] 2.3 Fix the 3 mislabeled cross-references: `#2-யாத்ருச்சிகப்படி` → `#12-யாத்ருச்சிகப்படி`
- [x] 2.4 Re-template the mistemplated errata row (item "47.") from `toc-row`/`toc-pg` to `p.toc-entry`, matching its sibling errata entries — **not** removed (corrected from the original plan; see proposal.md/design.md)
- [x] 2.5 Re-run the href/id cross-reference scan; confirm 0 broken links remain (excluding intentional bare `href="#"` search-jump links) — **confirmed: 0 broken**

## 3. Content cleanup (book-content-cleanup) — requires user confirmation before 3.3

- [x] 3.1 Extract occurrences of "பக்கம் ப்ரமாணம் காண்க" with context — **found all 187 confined to lines 5077-5869, entirely inside the "அஷ்டாதச ரஹஸ்ய ப்ரமாணத்திரட்டு" (proof-compilation) appendix (heading line 4526, close line 5873), which the book's own TOC lists as having independent pagination "1-185"**
- [x] 3.2 Present finding to the user: this reads as the appendix's own structural marker, not a placeholder — recommendation was "leave as-is"; **user reviewed and explicitly overrode this, confirming removal** (pasted several occurrences including the "3 & 4" variant)
- [x] 3.3 Removed all 192 occurrences (187 exact "பக்கம் ப்ரமாணம் காண்க" + 5 variants with inserted content, e.g. "பக்கம் ப்ரமாணம் 3 &amp; 4 காண்க", "பக்கம் ப்ரமாணம் I காண்க"). Left the distinct "பக்கம் ப்ரமாணம் Nல் பார்க்கவும்" phrasing (1 occurrence) untouched — different verb, not confirmed by the user. Cleaned up 2 resulting dangling empty-bracket artifacts and 48 now-empty `<p>` tags.
- [x] 3.4 Verified via word-level diff against `docs/index.html`: after fixing a self-introduced regression (a punctuation-cleanup regex had collapsed CSS rule-boundary newlines in the `<style>` block, and one blind substring-based revert hit the wrong duplicate word) and re-diffing until clean, confirmed zero unintended text changes anywhere else in the 6,101-line file
- [x] ~~3.5 Find and renumber the 9 duplicate-consecutive index-number pairs~~ — **retracted**: verified these are page-number references in a name index (different names sharing one page), not a numbering bug. Not a duplicate; not touched.
- [x] 3.6 Resolve the 1 ditto-mark entry ("165. ,,") to the preceding row's content ("அர்ஜுனன்") — **done**
- [ ] 3.7 Split/line-break the run-on multi-citation index cells (e.g. the "நஞ்ஜீயர்" entry) into separated sub-entries
- [x] 3.8 (found during 4.8 review, not originally planned) Fixed 4 paragraphs containing a literal leaked "**:::Center**" markdown-conversion artifact — stripped the artifact text and wrapped in the book's existing `.text-center` div convention

## 4. Semantic formatting (book-semantic-formatting)

- [x] 4.1 Change `<h3 class="chapter-heading">` → `<h2 class="chapter-heading">` (199 occurrences) — CSS selector `h2.chapter-heading` already exists, no CSS change needed
- [x] 4.2 Change `<h4 class="section-heading">` → `<h3 class="section-heading">` (9 occurrences) — same rationale
- [x] 4.3 Re-run the heading-level scan; confirm no skipped levels remain — **confirmed: h1→h2→h3, no old tags remain**
- [x] 4.4 Screenshot a chapter heading before/after in light theme to confirm the border/color/spacing now actually renders — **confirmed: `border-bottom` went from `0px none` to `2px solid`, margin-top from `0px` to `55.68px`**
- [x] 4.5 Verify the existing `h2.chapter-heading{page-break-before:always}` print rule now fires — **confirmed via print-media emulation: `page-break-before: page`**
- [x] 4.6 Change body `p{}` rule: `text-align:justify` → `text-align:left`; remove `hyphens:auto`
- [x] 4.7 Screenshot the same paragraph used in investigation (justify-rivers example) before/after to confirm even word-spacing — **confirmed visually**
- [x] 4.8 Classified all 1,153 paragraphs in the ப்ரமாணத்திரட்டு appendix (lines 4526-5873): 165 sutra-numbered citation openers, 518 verse-continuation/reference lines, 272 bracketed Tamil translations, 92 section/page dividers, 106 paragraphs containing the still-on-hold "பக்கம் ப்ரமாணம் காண்க" text (left completely untouched)
- [x] 4.9 Added `.cite-verse` (italic), `.cite-trans` (indented + left border), `.pg-ref` (small badge for inline "பக்கம்-N" page markers), `.appendix-marker` (small centered label) and applied them mechanically per the 4.8 classification — verified via word-level diff against `docs/index.html` that zero wording changed anywhere in the file, only the 187-hold text and markup/CSS
- [x] 4.10 Spot-checked in light, sepia, and dark themes, and at 390px mobile width — verse italics, translation indent/border, and page-ref badges all render correctly and legibly in every theme and at mobile width

## 5. Verification

- [x] 5.1 Run full regression: search feature works unmodified in `docs/index_v1.html` — **note**: the transliteration/Sarvam-AI search enhancement from earlier this session is no longer present in `docs/index.html` (working tree matches `git diff HEAD` exactly, i.e. reverted to last commit — outside this change's scope); verified the base search (literal Tamil query → 1/138 matches) and index-page click-through (→ 1/1 match, fresh load) both work correctly in `docs/index_v1.html`
- [x] 5.2 Screenshotted: chapter heading style restored (light/sepia/dark), justify-fix, citation/translation formatting, page-ref badges, mobile width — all confirmed correct
- [x] 5.3 Confirmed `docs/index.html` untouched: `git diff --stat docs/index.html` is empty; `git status` shows only `docs/index_v1.html`, `openspec/`, `.claude/` as new/untracked

## 6. Post-promotion refinements (after user renamed index_v1.html to index.html)

- [x] 6.1 Redesigned citation-appendix borders: verse+translation now share one continuous left-border/background per numbered entry (was: border only on the translation, looking disconnected) — verified pixel-continuity at entry seams, and clean breaks before each new numbered entry, in light/sepia/dark themes
- [x] 6.2 Fixed a regression from the earlier `<style>`-block reconstruction: it had pulled `text-align:justify;hyphens:auto` back in from the reverted baseline, silently undoing the earlier justify fix, plus corrupted the `.cite-trans`/`.pg-ref` margin and padding shorthands — all restored
- [x] 6.3 Fixed 68 running page-header artifacts (page number + OCR-garbled repetition of the book's own title, e.g. "அஷ்டாத௨ ரஹஸ்யம்") disguised as fake numbered citation entries, found throughout the whole book (27 in the appendix, 41 in the main commentary) — replaced with plain `பக்கம் N` page markers; verified no other genuine short sutra points were affected and no unintended text changes via word-level diff
- [x] 6.4 Committed and pushed to `feature/openspec` on GitHub (`.claude/settings.local.json` excluded, no secrets in the pushed commit — verified before push)

## 7. Second user-flagged formatting pass (user pasted screenshots/text of remaining bad spots)

- [x] 7.1 Found and fixed 56 additional appendix paragraphs that never got the citation-formatting pass in section 4 (root cause not fully determined — likely a gap in the original classification's boundary detection). Several bundled 3-4 citations into one unstyled run-on `<p>` (e.g. a Ramayana passage with 4 separate slokas+translations concatenated). Wrote a proper splitter: extracts leading/embedded "பக்கம்-N" markers as badges, splits remaining text on `[source][translation]` double-bracket boundaries into individual `cite-verse`/`cite-trans` paragraphs. Verified via word-level diff against the original baseline that wording is unchanged, only structure/markup added.
- [x] 7.2 Fixed a mistitled sub-heading: `<h2 id="ப்ரமாணத்திட்டு">` → `ப்ரமாணத்திரட்டு` (user-flagged spelling), including its sidebar TOC link/data-id.
- [x] 7.3 Fixed "பச்சம்" → "பக்கம்" typo in an errata note, and merged a duplicated citation (the same Subala Upanishad quote appeared twice in a row with two different OCR misreadings — "கிவ்யோ...[ஸுபால]" and "திவ்யோ...[ஸுபரல]" — into one clean, correctly-spelled citation + its translation, per the errata note's own instruction that it was providing "the correct version").
- [x] 7.4 Fixed 14 orphaned bare page-reference entries in the citation concordance/index (`<ul class="content-list">`, 874 `<li>` entries) where a continuation reference like "255-15" had been split into its own list item instead of being appended to the preceding word's entry (e.g. "அஜஸ்யநாபா: 254-10" + orphan "255-15" → "அஜஸ்யநாபா: 254-10, 255-15"). **Caught and fixed a duplication bug in the first attempt at this** (a naive dual-iterator merge approach caused the entire trailing "ஹ" letter-section, 14 entries, to be duplicated) — rewrote using direct position-based splicing, verified list count is exactly 874-14=860 with zero duplicates and zero remaining orphans.
- [x] 7.5 Fixed a stray artifact from 7.1's splitter: one translation ending in "]." had its trailing period spun off into its own empty-looking `<p class="cite-verse">.</p>` — merged back into the preceding translation paragraph.
- [x] 7.6 Re-verified end-to-end: JS syntax valid, 0 broken links, word-level diff against the original baseline shows only intended changes (all previously-listed fixes plus this section's), visually confirmed in browser.
