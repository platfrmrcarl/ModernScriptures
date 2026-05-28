# Modernize Residual Archaic Verses

**Date:** 2026-05-27
**Status:** Approved for planning

## Problem

`ModernScriptures.pdf` still contains chapters in archaic KJV English ("thee/thou/hath"). Root cause: 631 verses across the five books have `modernized=None` in `data/modernized/*.json`, and `scripts/render_pdf.py:34` falls back to italicized original text when the modernized field is empty.

Distribution of `modernized=None` verses:

| Book | Count | Total verses |
|---|---|---|
| kjv-ot | 348 | 23,145 |
| kjv-nt | 238 | 7,957 |
| dc | 34 | 3,654 |
| bom | 8 | 6,604 |
| pgp | 3 | 635 |
| **Total** | **631** | |

Inspection of `data/failed.jsonl` (653 log entries, 633 unique verses) shows the dominant failure mode is the `_proper_names` sanity check in `src/modern_scriptures/sanity.py`. Examples of false positives:

- `Gospel` → `gospel` (LLM lowercased a non-name theological term) → flagged "missing 'gospel'"
- `Remember that…` (sentence-start verb) → LLM rephrased; "Remember" not in output → flagged
- `Joseph Smith, Jun.` → `Joseph Smith Jr.` → "jun" missing → flagged
- `Beth-el` → `Bethel` → hyphen normalization mismatch → flagged
- `Trifle`, `Presidency`, `Angels`, `Cherubims` — same pattern (capitalized in source but legitimately not preserved verbatim)

A smaller real-issue bucket exists: genuine name swaps (`Sarai` → `Sarah`, `Cherubims` → `Cherubim`) and two length-overruns in D&C 77:9 and 113:1 (Q&A verses where the LLM expanded substantively).

## Goal

Eliminate archaic English from the rendered PDF, by (a) reducing the rate at which legitimate modernizations are rejected, then (b) guaranteeing a deterministic fallback for any verse that still has no LLM output.

## Approach

Belt-and-suspenders, three layers:

1. **Loosen the sanity gate** so legitimate modernizations stop being rejected.
2. **Re-run the modernizer** on the residual `None` verses (idempotent — only retries failures).
3. **Add a deterministic regex-based fallback** at render time, used only when a verse is still `None` after re-run.

## Detailed Design

### 1. Sanity-check changes (`src/modern_scriptures/sanity.py`)

Three targeted changes:

**1a. Substring check instead of regex re-extraction from output.**
Current behavior runs `_PROPER_NAME_RE` against both original and output, lowercases the resulting tokens, and does a set-difference. This means an output that legitimately lowercases `Gospel` → `gospel` is flagged, because `gospel` (lowercase) doesn't match the `[A-Z]…` regex in the output set.

New behavior: extract capitalized tokens from the original (same as today, minus `_COMMON_CAPS`), then for each, check `token.lower() in output.lower()` as a substring presence test. The output side no longer runs through the regex.

**1b. Normalize hyphens** in both original tokens and the output before substring matching, so `Beth-el` → `bethel` matches output `Bethel`. Implementation: `token.replace("-", "")` on both sides of the comparison.

**1c. Expand `_COMMON_CAPS`** with the high-frequency false-positives observed in `failed.jsonl`. Add (lowercase form): `jun`, `trifle`, `remember`, `lay`, `think`, `whoso`, `whosoever`, `presidency`, `concern`, `according`, `forever`, `justice`, `gather`, `order`, `heart`, `pure`, `state`, `stem`, `may`, `higbee`, `questions`, `revelation`, `what`, `esaias`, `amen`, `said`, `shall`, `was`, `die`, `cold`, `blood`, `innocent`, `murdered`, `angels`.

Real name swaps like `Sarai` → `Sarah` will still fail the gate. That's intentional — those are genuine information losses; the renderer's fallback (layer 3) will handle them so they don't appear archaic to the reader, but they remain visible in `failed.jsonl` for future manual review.

### 2. Re-run modernization

No code change. After 1 ships, run:

```
python scripts/modernize.py --all
```

`src/modern_scriptures/walk.py` already skips verses where `modernized` is truthy, so this only retries the ~631 currently-`None` verses. Expected outcome: the bulk pass with the loosened gate. Note: re-running appends new entries to `data/failed.jsonl` — that is acceptable; the file is an append-only audit log.

### 3. Render-time regex fallback (`src/modern_scriptures/quick_modernize.py`, new module)

A pure-string deterministic modernizer used **only** when `verse.modernized` is `None`.

Implemented as an ordered list of `(re.Pattern, replacement)` tuples. Order matters: longer/more-specific rules run before shorter ones (e.g., `saith` before the generic `-eth` ending). Substitutions are word-bounded (`\b…\b`) and case-preserving in the simple sense: each rule has two entries, one for the lowercased form and one for the capitalized form (e.g., `\bthou\b` → `you`, `\bThou\b` → `You`). All-caps forms (`LORD`, `JEHOVAH`) are left untouched — the renderer already handles those upstream and they read as modern English.

Rule set:

| Class | Examples |
|---|---|
| Pronouns | `thee/thou/ye` → `you`; `thy` → `your`; `thine` → `yours` (or `your` before vowel — see below) |
| Aux verbs | `hath`→`has`, `doth`→`does`, `art`→`are`, `wilt`→`will`, `shalt`→`will`, `mayst`→`may`, `canst`→`can` |
| `-eth` endings (explicit) | `saith`→`says`, `cometh`→`comes`, `goeth`→`goes`, `knoweth`→`knows`, `doeth`→`does` |
| `-est` endings (explicit) | `knowest`→`know`, `sayest`→`say`, `doest`→`do`, `believest`→`believe` |
| Archaic adverbs | `wherefore`→`therefore`, `whence`→`from where`, `whither`→`where`, `hither`→`here`, `thither`→`there`, `howbeit`→`however`, `verily`→`truly` |
| Other | `unto`→`to`, `behold`→`look` |

**`thine` handling:** apply a single rule that looks ahead. Pattern `\bthine\s+([aeiouAEIOU])` → `your \1` (before vowel as adjective); plain `\bthine\b` → `yours` (as pronoun). Acceptable approximation; the residual count is small.

**No generic `-eth` / `-est` stripping.** Stripping these endings programmatically (e.g., `\b(\w+)eth\b` → `\1s`) over-fires on words like `Elizabeth`, `meeketh` → bad output. Keep the explicit list above; anything not on the list stays as-is. Acceptable: this is a fallback, not a primary modernizer, and the residual after layers 1 and 2 should be small.

**Render integration (`scripts/render_pdf.py`):**

`_verse_paragraph` change: when `v.modernized` is falsy, call `quick_modernize(v.original)` and render in the normal verse style (drop the italics — the fallback prose reads as primary text, and italics would visually flag what we're trying to make invisible).

```python
def _verse_paragraph(v, style):
    body = v.modernized if v.modernized else quick_modernize(v.original)
    return Paragraph(f'<font size=8><super>{v.verse}</super></font> {body}', style)
```

### 4. Tests

- `tests/test_sanity.py` — add cases:
  - `Gospel` in original, `gospel` in output → passes (substring match)
  - `Beth-el` in original, `Bethel` in output → passes (hyphen normalization)
  - `Sarai` in original, `Sarah` in output → still fails (genuine name swap)
  - Each new `_COMMON_CAPS` entry: a representative verse passes when the LLM rephrases away the sentence-start word
- `tests/test_quick_modernize.py` (new) — table-driven tests covering each rule class, including:
  - case-preservation (`Thou` → `You`, `thou` → `you`)
  - word boundaries (`Elizabeth` is not mutated by any `-eth` rule)
  - `thine` before vowel vs. as pronoun
  - one full-verse end-to-end check on a known un-modernized Matthew verse
- `tests/test_render_pdf.py` — assert that when a verse has `modernized=None`, the rendered body comes from `quick_modernize` (not the raw original wrapped in `<i>`)

### 5. Execution order

1. Implement and test the sanity loosening (layer 1).
2. Re-run `python scripts/modernize.py --all` and observe drop in `None` count.
3. Implement `quick_modernize` module + renderer change + tests (layer 3).
4. Re-render the PDF: `python scripts/render_pdf.py`.
5. Spot-check 3-5 previously-archaic chapters (Genesis 1, Matthew 5, D&C 1, Moses 1, plus one randomly sampled from the residual `None` list) by reading the relevant pages in the new PDF.

## Out of Scope

- Improving the LLM prompt or switching models. The current prompt and gemma4 model are producing good output in most cases; the loss is at the gate, not at the model.
- Fixing the genuine name-swap cases (`Sarai`/`Cherubims`/etc.) at the LLM level. The fallback covers reader-facing presentation; deeper fidelity work is a separate effort.
- Restructuring `failed.jsonl` as anything other than an append-only audit log.

## Acceptance Criteria

- After steps 1-4, every verse rendered in the PDF is in modern English (no `thee/thou/thy/hath/saith/-eth` endings visible in the body text of any chapter).
- All existing tests pass; new tests added per section 4 pass.
- A re-run of `python scripts/modernize.py --all` is a no-op on already-modernized verses.
