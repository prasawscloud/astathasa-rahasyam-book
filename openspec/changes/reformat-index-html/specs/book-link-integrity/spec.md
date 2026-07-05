## ADDED Requirements

### Requirement: Every internal href resolves to an existing anchor
`docs/index_v1.html` SHALL contain no `href="#..."` (excluding bare `href="#"` used intentionally by the JS-driven search-jump index links) whose target has no matching `id="..."` element in the same document.

#### Scenario: TOC page-range links land on the correct chapter
- **WHEN** a reader clicks a table-of-contents page-range link such as `href="#pg-1"`
- **THEN** the browser SHALL scroll to the heading of the chapter/sub-section whose printed range (per the TOC's own text) contains that page number, not to a non-existent anchor

#### Scenario: Cross-reference links use the correct chapter id
- **WHEN** the document references chapter 12 (யாத்ருச்சிகப்படி) from the introduction (line ~671), the TOC (line ~732), or the chapter's closing line (line ~2585)
- **THEN** the link SHALL point to `#12-யாத்ருச்சிகப்படி`, matching the actual heading id, not `#2-யாத்ருச்சிகப்படி`

#### Scenario: No dead single-hash links remain from corrupted rows
- **WHEN** the corrupted TOC row (item 47, "18 அயடைய" / "அடைய") is processed
- **THEN** it SHALL either be removed or repointed to a real anchor — it SHALL NOT remain as a link with `href="#"` and no functional target

### Requirement: Link-integrity fixes are verifiable by automated scan
A scripted href-vs-id cross-reference scan (the same method used to find the original 47 broken links) SHALL report zero broken internal links when run against `docs/index_v1.html`.

#### Scenario: Post-fix verification
- **WHEN** the href/id cross-reference scan is re-run after fixes are applied
- **THEN** the count of hrefs with no matching id SHALL be 0 (excluding intentional bare `href="#"` search-jump links)
