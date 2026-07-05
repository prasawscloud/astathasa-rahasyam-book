## ADDED Requirements

### Requirement: Sequential heading hierarchy
`docs/index_v1.html` SHALL use a heading hierarchy with no skipped levels: `h1` (book title) → `h2` (chapter headings, currently `.chapter-heading`) → `h3` (section headings, currently `.section-heading`).

#### Scenario: Heading level scan shows no skips
- **WHEN** all heading tags in `docs/index_v1.html` are extracted in document order
- **THEN** no heading SHALL be nested more than one level below its preceding heading of a shallower level (i.e. no h1→h3 or h2→h4 jumps)

#### Scenario: Print page-break rule fires correctly
- **WHEN** the document is rendered for print
- **THEN** each chapter (now `h2.chapter-heading`) SHALL start on a new printed page, per the existing `h2.chapter-heading{page-break-before:always}` CSS rule, which is currently dead code because chapter headings are `h3`

### Requirement: Body paragraphs use Tamil-appropriate alignment
Body paragraph text in `docs/index_v1.html` SHALL be left-aligned (not justified), and SHALL NOT rely on CSS hyphenation for Tamil script.

#### Scenario: No justify-induced whitespace rivers
- **WHEN** a body paragraph is rendered at the book's default reading width
- **THEN** inter-word spacing SHALL be uniform (browser default word-spacing), not stretched unevenly to fill the line
- **AND** the paragraph rule SHALL NOT set `hyphens: auto`

### Requirement: Index-appendix entries are internally readable
No single index-entry cell SHALL present multiple distinct sub-citations as an unbroken run of text with no separating structure.

#### Scenario: Concatenated citations are split
- **WHEN** an index entry (such as the "நஞ்ஜீயர்" entry) originally packs several distinct page-citation groups into one cell with no breaks
- **THEN** each distinct sub-citation group SHALL be separated by a line break or its own row, consistent with the single-entry-per-row pattern used elsewhere in the same index

### Requirement: Quoted verse/citation text is visually distinct
Within long commentary paragraphs, inline Sanskrit verse citations and their bracketed translations SHALL be styled distinctly from the surrounding Tamil prose, without changing any wording.

#### Scenario: Citation block is visually distinguishable
- **WHEN** a paragraph contains an inline Sanskrit ஸ்லோகம் citation with source reference (e.g. `[தை. நா-11]`) and bracketed translation
- **THEN** that span SHALL render with a distinct style (e.g. italics, indent, or bordered block) from the commentator's own prose in the same paragraph
- **AND** the underlying text content SHALL be byte-identical to the source (styling only, no wording changes)
