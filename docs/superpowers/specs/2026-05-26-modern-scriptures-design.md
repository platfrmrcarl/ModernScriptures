# Modern Scriptures — Design

## Goal

Produce a single PDF (`ModernScriptures.pdf`) containing the four LDS Standard
Works — KJV Bible, Book of Mormon, Doctrine and Covenants, Pearl of Great
Price — rewritten verse-by-verse from archaic English into clear contemporary
English in the style of the NIV/ESV.

## Decisions made during brainstorming

| Decision | Choice |
|---|---|
| Scope | All four standard works |
| Style | Conservative (NIV/ESV-like); preserve meaning, not paraphrase |
| Content | Verse text only — no chapter headings, no footnotes, no study aids |
| Execution | Pilot on Pearl of Great Price first, then run the remaining three |
| Model | `gemma4:26b` via local Ollama |
| Source text | Canonical public-domain text fetched from a known clean source |

## Non-goals

- Reproducing the LDS edition's chapter/section summaries, footnotes, JST
  excerpts, Bible Dictionary, Topical Guide, or maps. These are copyrighted by
  Intellectual Reserve, Inc.
- Matching the exact two-column layout of the source PDF.
- Verse-level theological commentary or interpretation.

## Architecture

Three independent scripts run in sequence. Intermediate JSON files between
them so each step is independently runnable, debuggable, and resumable.

```
scripts/
  fetch_source.py     # canonical PD text     → data/source/<book>.json
  modernize.py        # walk verses, call LLM → data/modernized/<book>.json
  render_pdf.py       # modernized JSON       → ModernScriptures.pdf
data/
  source/             # one JSON per book (kjv-ot, kjv-nt, bom, dc, pgp)
  modernized/         # one JSON per book; partial files OK
  failed.jsonl        # verses that failed sanity checks after retries
ModernScriptures.pdf  # final output
```

**Unit boundaries:**
- `fetch_source.py` is the only step that touches the network.
- `modernize.py` is the only step that talks to Ollama.
- `render_pdf.py` is the only step that produces a PDF.

## Data shape

Uniform across all four works:

```json
{ "book": "1 Nephi", "chapter": 1, "verse": 1,
  "original":   "I, Nephi, having been born of goodly parents…",
  "modernized": null }
```

`modernize.py` fills in `modernized` and writes after each verse. Crash or kill
loses at most the verse in flight. Re-running skips verses where `modernized`
is already populated.

## Source-text fetch (`fetch_source.py`)

Outputs five JSON files:

- `data/source/kjv-ot.json`
- `data/source/kjv-nt.json`
- `data/source/bom.json`
- `data/source/dc.json`
- `data/source/pgp.json`

**Source candidates (all public domain):**
- KJV → `aruljohn/Bible-kjv` or `scrollmapper/bible_databases` on GitHub.
- BoM / D&C / PoGP → `bcbooks/scriptures-json` or an equivalent.

The fetcher:
1. Downloads the source data.
2. Normalizes to the uniform `{book, chapter, verse, original}` shape.
3. Writes JSON.
4. Spot-checks a few sampled verses against the source PDF and reports any
   wording differences (LDS-edition KJV has minor printer's-error fixes vs.
   non-LDS KJV editions in a few OT verses).

If a source URL is dead at runtime the script fails loudly and we swap in
an alternate.

## Modernization (`modernize.py`)

### Prompt

A single system prompt with a few-shot exemplar; per-call user message is
just the verse text.

```
You are modernizing archaic English scripture into clear contemporary English
in the style of the NIV or ESV. Rules:
- Replace thee/thou/thy/ye and -eth/-est verb endings.
- Replace archaic vocabulary (e.g. "wherefore" → "therefore",
  "whence" → "from where").
- Keep proper names exactly as written.
- Preserve theological terms when they have no plain equivalent (covenant,
  iniquity, atonement, etc.).
- Preserve sentence boundaries and meaning faithfully. Do NOT paraphrase.
- Do not add or remove content. Do not explain. Do not add quotation marks.
- Output ONLY the modernized verse, nothing else.

Example:
INPUT:  And it came to pass that I, Nephi, said unto my father:
        I will go and do the things which the Lord hath commanded.
OUTPUT: I, Nephi, said to my father: I will go and do the things
        the Lord has commanded.
```

One verse per call. No batching across verses — gemma4:26b is more consistent
on small units, and the resume-on-crash story is simpler.

### Sanity checks (per verse)

Applied before writing `modernized` to disk:
1. Output length is between 0.4× and 2.5× input length.
2. All capitalized proper-name tokens from the input appear in the output.
3. Output does not start with quote marks, "Sure,", "Here is", "The verse",
   or other common preamble openings.

A verse failing sanity checks is retried up to 3 times with a slight prompt
nudge. After 3 failures it's logged to `data/failed.jsonl` and left with
`modernized: null`. Re-runs will retry it.

### Throughput estimates

- gemma4:26b on consumer GPU: ~10–30 tok/s.
- ~41,000 verses total, ~25 output tokens per verse ≈ ~1M output tokens.
- Estimated full run: 15–30 hours.
- Pearl of Great Price pilot: ~635 verses ≈ 30–90 minutes.

These will firm up after the pilot run.

## PDF rendering (`render_pdf.py`)

Library: ReportLab (Python, no external font dependencies, handles long docs
and PDF bookmarks).

Layout:
- Page size 6"×9", single column, generous margins.
- Title page.
- Table of contents (hyperlinked, one entry per book).
- Each book begins on a new page with the book title.
- Chapters as H2.
- Verses as numbered paragraphs: small superscript verse number, then text.
- Built-in serif (Times) for body, sans for headings.

No footnotes, no cross-references, no study aids.

## Pilot then full

1. Build all three scripts.
2. Run end-to-end on Pearl of Great Price only.
3. Inspect modernized output and the generated PDF.
4. Adjust prompt, sanity checks, or layout based on what we see.
5. Run the remaining three books.

## Risks and mitigations

- **Quality drift on long-running local inference.** Mitigation: sanity checks
  per verse + spot review of pilot output before committing to full run.
- **Ollama crash or machine reboot mid-run.** Mitigation: write-after-each-verse
  persistence; idempotent re-run skips completed verses.
- **Source-text mismatch with PDF edition.** Mitigation: fetch step spot-checks
  sampled verses and reports differences. For the LDS-specific KJV variants
  (a handful of OT verses), we'll accept the canonical KJV reading; this is
  noted, not silently smoothed over.
- **Copyright on LDS study aids.** Mitigation: explicitly excluded from scope.
