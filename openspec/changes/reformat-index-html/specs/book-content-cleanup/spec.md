## ADDED Requirements

### Requirement: Suspected artifact text is located and verified in context before any action
The system SHALL locate every occurrence of a suspected artifact string (e.g. "பக்கம் ப்ரமாணம் காண்க", 187 occurrences at time of writing) and verify where it actually occurs (surrounding headings, document structure, TOC entries) before concluding it is noise — not just pattern-match the string in isolation.

#### Scenario: Structural context overrides an isolated pattern-match
- **WHEN** a repeated string looks like a leftover placeholder from its text alone
- **THEN** the system SHALL check its location against document structure (e.g. is it confined to one distinctly-headed appendix with its own pagination?) before recommending removal
- **AND** if that structural check indicates the text is likely legitimate (as found for "பக்கம் ப்ரமாணம் காண்க", confined entirely to the book's own "ப்ரமாணத்திரட்டு" citation-compilation appendix), the default recommendation SHALL be to leave it, with the finding reported to the user for a final decision
- **AND** the user's explicit decision — in either direction — always overrides the system's recommendation (confirmed in practice: the user reviewed this exact finding and chose removal, which was then carried out per the "confirmed removal" requirement below)

### Requirement: Any confirmed removal is applied uniformly
If the user confirms removal of a specific artifact string after reviewing the evidence, the action SHALL be applied to every occurrence consistently — no partial or silently-different treatment between instances.

#### Scenario: Uniform removal if confirmed
- **WHEN** the user, after seeing the structural evidence, explicitly confirms removal of a given string
- **THEN** every occurrence SHALL be removed from `docs/index_v1.html`, including reasonable variants of the string (e.g. "பக்கம் ப்ரமாணம் காண்க" and "பக்கம் ப்ரமாணம் 3 &amp; 4 காண்க" are the same underlying artifact with different inserted content)
- **AND** the surrounding sentence/paragraph structure SHALL remain grammatically intact (no dangling punctuation, empty bracket pairs, or double spaces left behind)
- **AND** a distinctly-worded string that merely resembles the confirmed one (e.g. "பக்கம் ப்ரமாணம் Nல் பார்க்கவும்", a different verb) SHALL NOT be removed without separate confirmation

### Requirement: Mistemplated errata row uses the correct container
The row (originally item "47.") that was wrapped in the `toc-row`/`toc-pg` template SHALL instead use the same `p.toc-entry` template as its sibling errata entries (lines 5878+), preserving its original content ("18 அயடைய — பக்கம் அடைய") with the "—" separator its wrong template had dropped.

#### Scenario: Errata row matches sibling format
- **WHEN** `docs/index_v1.html`'s errata (பிழை - திருத்தம்) section is scanned
- **THEN** every entry, including item "47.", SHALL use the `<p class="toc-entry">` format
- **AND** no entry in that section SHALL be wrapped in `toc-row`/`toc-pg` markup

### Requirement: Index entries keyed by page number are not renumbered
Where an index's number column represents a page number (not a sequential item count), multiple consecutive entries legitimately sharing one page number SHALL be left as-is — this is not a duplication bug.

#### Scenario: Page-number-keyed repeats are preserved
- **WHEN** the name/subject index appendix has consecutive entries sharing the same number (e.g. two entries both "172.", confirmed to be different names both citing page 245 in their own body text)
- **THEN** neither entry's displayed number SHALL be changed

### Requirement: Ditto marks are resolved to their referenced content
An index entry whose entire content is a bare ditto mark (e.g. "165. ,,") SHALL be replaced with the actual content of the entry it refers to (the immediately preceding row), not left as an unresolved punctuation mark.

#### Scenario: Ditto entry shows real content
- **WHEN** the index entry originally reading "165. ,," is rendered
- **THEN** it SHALL display the same name/content as row "164." instead of a bare comma

### Requirement: Running page-header artifacts are reduced to a plain page marker
Where a numbered "sutra"-style paragraph's entire content is a running page-header artifact (the printed book's own title, OCR-garbled) rather than a real citation or doctrinal point, it SHALL be replaced with a plain page-number marker instead of being left to display as a fake numbered entry.

#### Scenario: Page-header noise is not mistaken for content
- **WHEN** a `<span class="sutra-num">N.</span>` paragraph's only content matches the pattern of the book's own (variously OCR-garbled) title — e.g. "அஷ்டாத௨ ரஹஸ்யம்", "அஷ்டாத, v0 ரஹஸ்யம்" — with nothing else in that paragraph
- **THEN** it SHALL be replaced with `<p class="appendix-marker">பக்கம் N</p>`, dropping the garbled title text
- **AND** this SHALL apply book-wide (not only within the citation-compilation appendix), since the artifact recurs throughout the main commentary too

#### Scenario: Genuine short sutra points are not touched
- **WHEN** a `<span class="sutra-num">` paragraph is short but is a genuine terse doctrinal point (e.g. "ஏகம்.", "பரித்யஜ்ய.")
- **THEN** it SHALL NOT be altered — only paragraphs matching the book-title artifact pattern are affected

### Requirement: No authorial or scriptural content is altered
Every content-cleanup action SHALL be scoped to the specific identified artifacts (the placeholder string, the one mistemplated errata row, the one ditto mark) — no other text in the book SHALL be reworded, reordered, or removed as a side effect.

#### Scenario: Byte-level diff outside flagged spans is empty
- **WHEN** `docs/index_v1.html` is diffed against `docs/index.html` with all confirmed-removed spans excluded
- **THEN** the remaining running text (sutras, commentary, citations) SHALL be identical
