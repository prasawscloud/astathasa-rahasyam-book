## Context

`docs/index.html` is a single static HTML file (no build step, no backend) published via GitHub Pages. It already carries a client-side search feature (offline itrans transliteration + optional Sarvam AI transliteration refinement) added in a prior change — that code and its embedded Sarvam API key are out of scope here and must keep working unmodified.

Verified findings that motivate this change (see proposal.md for full counts):
- 45/45 `href="#pg-N"` TOC links are broken — zero `id="pg-N"` anchors exist anywhere.
- No per-page markers exist in the digitized text at all (`class="page-ref"` occurs exactly once and is unrelated — a closing-statement style, not a page marker). So the original book's exact page boundaries were not preserved in this HTML.
- 3 cross-reference links use a wrong id prefix (`#2-...` instead of `#12-...`) — a straightforward off-by-mislabel, correct target exists.
- 1 TOC row (item 47) has corrupted title/link text from source conversion.
- "பக்கம் ப்ரமாணம் காண்க" appears 187 times — but entirely confined to lines 5077-5869, inside the book's own "அஷ்டாதச ரஹஸ்ய ப்ரமாணத்திரட்டு" (proof/citation-compilation) appendix (heading line 4526, close line 5873), which has its own internal pagination per the TOC. Likely a structural marker of that appendix, not a stray placeholder — see Decision 4.
- Heading levels skip h2 (`h1 → h3 chapter-heading → h4 section-heading`) — and because the CSS for these classes is tag-qualified (`h2.chapter-heading`, `h3.section-heading`), this mismatch means **the styling never applies at all**: measured via headless browser, a live chapter heading computes `border-bottom: 0px none`, `margin-top: 0px` — not the intended `2px solid` accent border and `2.4em` spacing. This is a rendering bug, not just a semantic one.
- `p{text-align:justify;hyphens:auto}` on all body paragraphs. `hyphens:auto` has no effect (no browser ships Tamil hyphenation rules). `text-align:justify` visibly stretches inter-word gaps into uneven "rivers" of whitespace — confirmed by rendering and screenshotting a real paragraph — because Tamil compound words are long, so few words fit per line and each justified line has only 2-4 stretch points.
- The 116 `<table class="idx-table">` fragments forming the proper-noun index appendix have inconsistent granularity (some hold many `<tr>` rows, some hold a single row) and at least one entry concatenates several sub-citations into one unbroken run-on cell; 9 places repeat the same index number on two different consecutive entries; 1 entry's content is a bare ditto mark ("165. ,,") left over from print typesetting.

## Goals / Non-Goals

**Goals:**
- Every internal link in `docs/index_v1.html` resolves to a real, correct anchor — no dead `#` targets.
- Re-template the mistemplated errata row (item 47) and remove all 192 "பக்கம் ப்ரமாணம் காண்க" occurrences and variants, per the user's explicit decision overriding the initial "leave as-is" recommendation.
- Sequential heading hierarchy (h1→h2→h3) with no skipped levels, restoring the currently-dead chapter/section heading border and spacing styling.
- Tamil-appropriate paragraph alignment: left-aligned instead of justified, no dead hyphenation property.
- Readable, unambiguous index-appendix entries: no run-on multi-citation cells, no duplicate index numbers, no bare ditto marks.
- Visually distinguish quoted Sanskrit verse/citation spans from the commentator's Tamil prose inside long paragraphs, without changing any wording.
- Zero data loss: every word of actual scripture/commentary content is preserved verbatim; only the specific artifacts listed above are touched.

**Non-Goals:**
- Not reconstructing the original book's true page numbers — that data doesn't exist in the source and inventing it would be fabrication, not a fix.
- Not touching `docs/index.html` — output is `docs/index_v1.html` only.
- Not re-running or modifying the search/transliteration feature (Sarvam AI key, itrans fallback) — carried over unchanged.
- Not a full OCR re-check of all ~3,920 paragraphs — out of scope; see Decisions for the narrower, targeted use of Sarvam AI.

## Decisions

**1. `#pg-N` links redirect to the nearest chapter/section anchor, not a reconstructed page anchor.**
Alternative considered: invent `id="pg-N"` anchors at estimated text offsets. Rejected — there's no marker in the source indicating where original page N actually starts; any offset would be a guess dressed up as data. Instead, since every TOC row already states its own page range next to a chapter title (e.g. `"#pg-1"` ↔ row "1—23" ↔ `முமுக்ஷுப்படி`), each `#pg-N` href is rewritted to the `id` of the chapter/sub-section heading whose printed range contains N. This is mechanical (derived straight from the TOC's own text) and makes every link land in the right neighborhood instead of nowhere.

**2. Fix the 3 mislabeled cross-references by correcting the id prefix.**
`#2-யாத்ருச்சிகப்படி` → `#12-யாத்ருச்சிகப்படி` (matching the real heading id at line 2558). Single find-replace, no ambiguity — the corrected target is an exact, already-existing heading id.

**3. Mistemplated errata row (item "47.") — re-template to match its siblings, don't delete.**
Initial read was "corrupted, unreconstructable, drop it." Wrong — reading the surrounding lines (5875-5889) shows this sits inside the book's own "பிழை - திருத்தம்" (errors/corrections) appendix, where every other entry uses `<p class="toc-entry"><strong>N.</strong> line original — பக்கம் corrected</p>`. Only this one entry got wrapped in the `toc-row`/`toc-pg` template instead (meant for the actual table of contents earlier in the document), which is why its number looked like a chapter index and its correction text looked like a broken page-link. Fixed by re-templating to the sibling format: `<p class="toc-entry"><strong>47.</strong> 18 அயடைய — பக்கம் அடைய</p>` — same content, correct container.

**4. Text ("பக்கம் ப்ரமாணம் காண்க", 187×) — investigated, found to look like legitimate structure, recommend leaving untouched.**
Original plan (before investigation) was to treat this as a leftover "insert citation here" placeholder and remove it on confirmation. Investigating where it actually occurs changed the conclusion: every one of the 187 occurrences sits inside the book's own "அஷ்டாதச ரஹஸ்ய ப்ரமாணத்திரட்டு" (proof/citation-compilation) appendix — a distinctly-headed, self-contained section (lines 4526-5873) that the book's own TOC says has its own internal pagination ("1 ப்ரமாணத்திரட்டு: 1-185"), and inside that appendix the phrase recurs at a steady density (~once per 4-5 lines) consistent with it being a structural entry-marker belonging to that appendix's own citation-listing format, not scattered leftover noise. Extracted all 187 occurrences with context for review regardless (task 3.1/3.2), but the recommendation reversed from "confirm removal" to "confirm leaving as-is." Not removed.

**5. Sarvam AI used narrowly, as a review aid — not a bulk rewrite tool.**
Per user's request to use Sarvam AI "if needed" for font/Tamil issues: available as a second-opinion tool for spot-checking any span still genuinely in doubt after direct investigation — not needed for Decision 4 in the end, since reading the surrounding structure (the ப்ரமாணத்திரட்டு appendix boundaries and its own TOC entry) was sufficient to change the recommendation without further tooling. "Font" itself is unrelated to Sarvam (it's a Google Fonts CSS choice, `Noto Serif/Sans Tamil`, already correct — see prior conversation) — no change needed there.

**6. Heading re-level: `chapter-heading` → h2, `section-heading` → h3, `book-title` stays h1.**
Pure tag-level rename (keep existing classes/styling), no visual change intended beyond what `h2`/`h3` default browser styling would imply — CSS already targets these by class, not tag, so re-leveling the tag is expected to be visually inert and purely structural/semantic.

**7. Citation/verse visual treatment: new `.cite` inline/block style, applied only to bracketed Sanskrit-verse-plus-translation spans identified during paragraph review**, not a blanket regex — long paragraphs mix free prose and citations irregularly enough that a manual/assisted pass per flagged paragraph is safer than a single global pattern.

**8. Body paragraph alignment: `text-align:justify` → `text-align:left`; drop `hyphens:auto`.**
Alternative considered: keep `justify` but add `text-align-last`/`word-spacing` tuning to reduce rivers. Rejected — partial fixes for justify-with-long-words are fragile and font/viewport-dependent; `text-align:left` is the standard, robust recommendation for Indic-script web typography and matches what the screenshot evidence calls for. This is a one-line, low-risk CSS change (single `p{}` rule, applies uniformly) with no content impact.

**9. Index run-on cells: insert line breaks between concatenated sub-citations.**
Where one `<td class="idx-body">` cell contains multiple distinct citations jammed together (identified by repeated `(page-number)` patterns with no separating punctuation/break), insert `<br>` or split into separate `<tr>` rows consistent with the single-row-per-entry pattern used elsewhere in the same index. No wording changes — purely inserting structure that's already implied by the repeated citation pattern.

**10. Ditto mark: resolve; "duplicate" index numbers: leave untouched — they're not duplicates.**
Initial read treated the 9 places where the same number repeats on consecutive entries (e.g. two entries both "172.") as a numbering bug to renumber. Wrong, caught before applying: this column is a **page number**, not a sequential item count — it's a name/subject index organized by page, and several different names legitimately share one printed page (verified: entries numbered "323./323./324./324./324." are five different names, each independently citing page 245 in their own body text). "Fixing" this would have overwritten real page-reference data with a fabricated sequence. Not touched.
For the single ditto-mark entry ("165. ,,"), this *is* a real artifact — replaced with the actual name from the immediately preceding row ("அர்ஜுனன்", row "164."), matching the standard print-index ditto convention ("same name as above, different page"). This one's mechanical and unambiguous; the duplicate-number one was not a bug at all.

## Risks / Trade-offs

- **[Risk] Rewriting `#pg-N` targets to chapters, not exact pages, may still disappoint a reader expecting page-accurate navigation.** → Mitigation: this is strictly better than the current 100%-broken state, and is explicitly scoped as a known limitation (no exact page data exists) rather than presented as page-perfect.
- **[Risk avoided] Removing the 187 "பக்கம் ப்ரமாணம் காண்க" occurrences would very likely have destroyed legitimate appendix structure.** → This was the original plan; investigating where the phrase actually occurs (entirely within one self-contained, separately-paginated citation appendix) reversed the recommendation before any deletion happened. No text removed for this item.
- **[Risk] Heading re-level could interact with existing print CSS (`h2.chapter-heading{page-break-before:always}` at line 348 already targets h2 — currently a dead rule since chapter headings are h3!).** → Mitigation: this actually reveals a second latent bug (the print page-break rule has never fired); re-leveling to h2 fixes it as a side effect, but must be verified visually in the print preview.
- **[Risk] Touching a 6,100-line single file by hand risks introducing new breakage.** → Mitigation: all mechanical fixes (link rewrites, id corrections, heading tags) done via scripted find/replace with before/after counts verified (same approach used to find them), not manual line editing; content-area changes (citation styling) scoped to flagged spans only.
- **[Risk] Restoring heading styling (Decision 6) will visibly change the appearance of all 199 chapters at once — a dramatic, book-wide visual shift, even though it's "just" a bug fix.** → Mitigation: screenshot before/after in all three themes (light/sepia/dark) and print preview before considering this done; since the CSS itself is unchanged (only the tag now matches it), the result is deterministic, not a new design being invented.
- **[Risk demonstrated, not hypothetical] Assuming a pattern is a "bug" from static reading alone, without checking what it actually represents.** → This happened twice in this same change: the "47." TOC row (Decision 3) and the "duplicate" index numbers (Decision 10) were both initially misdiagnosed by pattern-matching alone and corrected only after reading surrounding context / cross-checking the data. Mitigation going forward: verify against neighboring content before applying any "fix" that changes or removes visible text, not just against the isolated pattern that flagged it.

## Open Questions

1. ~~Confirm disposition of the 187 "பக்கம் ப்ரமாணம் காண்க" occurrences~~ — **resolved**: user reviewed the finding and explicitly confirmed removal, overriding the "leave as-is" recommendation. All 192 occurrences (187 + 5 variants) removed; see proposal.md and tasks.md 3.1-3.4.
2. Should the corrected `#pg-N` chapter-level redirects be visually flagged to the reader (e.g. tooltip "approximate location") or silent? Default assumption: silent, since exact-page framing was never accurate to begin with.
