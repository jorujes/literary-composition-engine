---
name: literary-composition-engine
description: Use when building, testing, or running the Hermes-native literary composition experiment end to end: prepare a literary corpus, derive theme/style contracts and evidence, validate an author pack, and generate high-style long-form prose through blueprinting, paragraph planning, neutral drafts, literal source-sentence anchoring, audit, and repair.
version: 0.1.0
author: Hermes Competition Team
license: MIT
metadata:
  hermes:
    tags: [creative, writing, literary-composition, corpus, subagents, sqlite, anti-slop]
    category: creative
    related_skills: [humanizer, subagent-driven-development, hermes-agent-skill-authoring]
---

# Literary Composition Engine

## Overview

Build an editable author model from a messy literary corpus, then use that model as a high-style literary composition benchmark. Literary mimicry is the hardest evaluation surface: success requires control over world, knowledge, paragraph logic, sentence architecture, and phrase-level pressure. The same machinery then becomes useful anywhere durable style matters.

The core thesis is that style becomes executable when it is decomposed into artifacts: corpus evidence, theme cards, style cards, source-sentence anchors, paragraph plans, audits, and repair moves.

The full workflow has four production phases plus one mandatory final repair
gate before release:

1. **Phase 1: Corpus Preparation**: raw source files -> `corpus/<author>.db` with stories, paragraphs, sentences, and source sentence anchors.
2. **Phase 2: Author Pack Construction**: corpus -> `theme.contract.yaml`, `style.contract.yaml`, `evidence.notes.yaml`, and `instruction.pairs.yaml`.
3. **Phase 3: Artifact Validation & Calibration**: contracts/evidence -> validated author pack with release gate and runtime flags.
4. **Phase 4: Writing Runtime**: user request -> outline/blueprint/paragraph plan -> neutral draft -> sentence-by-sentence source anchoring -> audited assembled prose.
4.5. **Phase 4.5: Final Text Repair**: assembled prose -> local error repair, false-positive repair reversal, final repair audit, and approved output for release.

The operator should be able to give Hermes an author, source files, and a writing request. Hermes must run the phase workflow without requiring manual steering between internal steps. All semantic/editorial decisions are made by agents. Python tools only persist, count, list, validate structure, index, and assemble already released artifacts.

Core rule:

```text
agents decide; Python persists
```

## When to Use

Use this skill when the user wants to:

- prepare or inspect an author corpus for the hackathon project
- build `corpus/<author>.db` from `.txt`, `.pdf`, `.epub`, or `.docx` source material
- run discovery, extraction, cleanup, or validation subagents
- derive `theme.contract.yaml`, `style.contract.yaml`, `evidence.notes.yaml`, and `instruction.pairs.yaml` from an approved corpus
- validate an author pack before generation
- run the Phase 4 writing runtime with outlines, blueprint, paragraph plans, sentence anchors, audits, repairs, and release gates
- run the Phase 4.5 final text repair gate before final release
- avoid parser-driven literary ingestion

Do not use this skill for generic text rewriting without a corpus and validated author pack. Use a direct editing workflow for that.

## Directory Layout

Expected project-local layout:

```text
sources/<author>/                         # raw source files
corpus/<author>.db                        # Phase 1 output
author-models/<author>/                   # contracts, evidence, validation, validated pack
runs/<author>/<run_id>/                   # phase runs and writing outputs
```

Inside this skill:

```text
scripts/corpus_db.py                      # mechanical SQLite tool
scripts/validate_phase4_run.py            # mechanical Phase 4 release validator
references/artifact-schemas.md            # generated artifact locations and required files
references/prompts/discover_stories.md    # discovery agent prompt
references/prompts/extract_story.md       # extraction agent prompt
references/prompts/cleanup_story.md       # cleanup agent prompt
references/prompts/validate_story.md      # validation agent prompt
references/prompts/run_phase2_author_pack.md         # Phase 2 orchestration prompt
references/prompts/run_phase3_validation.md          # Phase 3 orchestration prompt
references/prompts/run_phase4_writing_runtime.md     # Phase 4 orchestration prompt
references/prompts/audit_phase4_sentence_anchor.md   # independent sentence anchor audit prompt
references/prompts/run_phase4_sentence_anchor_repair_pass.md # final anchor repair/lock prompt
references/prompts/run_phase45_final_text_repair.md  # story-level final text repair prompt
```

Generated DBs, YAML author packs, validation reports, and run artifacts belong
in the user's active workspace. See `references/artifact-schemas.md`.

## Phase 1 Workflow

### 0. Operator Contract

The human/operator should only need to provide:

```text
author slug
source file or source directory
working directory
```

Hermes is responsible for creating `corpus/<author>.db` if it does not exist. Do not ask the user to initialize the DB manually.

### 1. Create the Author DB

```bash
python3 ${HERMES_SKILL_DIR}/scripts/corpus_db.py init --db corpus/<author>.db
```

This creates:

- `stories`
- `paragraphs`
- `paragraphs_fts`
- `sentences`
- `sentences_fts`
- `ingestion_log`

Status source of truth:

- `stories` stores accepted story metadata and word counts only.
- `paragraphs` stores accepted paragraph text only.
- `sentences` stores accepted sentence text and paragraph/story position.
- `ingestion_log` stores ingestion state: `pending`, `done`, or `needs_review`.
- Any pending/review/done query must read `ingestion_log`, not `stories`.
- Reports that combine text metadata with status should join `stories.story_id` to `ingestion_log.story_id`.

### 2. Dispatch Discovery

Use `delegate_task` with the contents of `references/prompts/discover_stories.md`.

The discovery agent reads source files and returns a JSON manifest. It decides:

- which works are present
- their order
- candidate `story_id`
- title / collection / publication year when available
- source path
- risks and exclusions

The parent then writes pending entries through the DB tool:

```bash
python3 ${HERMES_SKILL_DIR}/scripts/corpus_db.py load-manifest \
  --db corpus/<author>.db \
  --manifest runs/<author>/<run_id>/manifest.json
```

### 3. Dispatch Extraction in Parallel

Hermes `delegate_task` uses the configured `delegation.max_concurrent_children` limit from `config.yaml` or `DELEGATION_MAX_CONCURRENT_CHILDREN`. Before a corpus run, set that limit to the desired concurrency. For independent story extraction, prefer one extraction subagent per pending story whenever the runtime permits it. Use waves only as a fallback when the configured/runtime limit is lower than the number of pending stories.

Get pending work:

```bash
python3 ${HERMES_SKILL_DIR}/scripts/corpus_db.py list \
  --db corpus/<author>.db \
  --status pending
```

Each extraction subagent receives:

- author slug
- absolute source path
- target `story_id`
- title / collection / year if known
- exclusion rules
- required artifact JSON schema
- output path under `runs/<author>/<run_id>/extracted/`

Use `references/prompts/extract_story.md`.

The parent persists a completed extraction:

```bash
python3 ${HERMES_SKILL_DIR}/scripts/corpus_db.py ingest-story \
  --db corpus/<author>.db \
  --story-json runs/<author>/<run_id>/extracted/<story_id>.json
```

### 4. Cleanup and Validation

If an extraction has low confidence or visible source problems, dispatch cleanup/validation agents using:

- `references/prompts/cleanup_story.md`
- `references/prompts/validate_story.md`

Agents decide whether the result is `done` or `needs_review`. The DB tool only records that decision.

Validation artifacts must use a strict schema:

- `validated_status` must be exactly `done` or `needs_review`; do not use `valid`, `validated`, `ok`, `passed`, or `failed`.
- `cleaned_story_json` must be a string path to a cleaned JSON artifact or `null`; never embed a story JSON object in this field.
- If cleanup is needed, write the cleaned story to `runs/<author>/<run_id>/cleanup/` and reference that path.
- The parent must not ingest an artifact until the corresponding validation artifact has `validated_status: "done"`.

Epigraphs, dedications, authorial date lines, and other authorial paratext inside a story chapter are story material by default. Exclude them only when the validation agent can identify them as publisher/editor/translator matter rather than authorial text.

### 5. Rebuild Sentence Index

After all accepted stories are persisted, rebuild sentence rows:

```bash
python3 ${HERMES_SKILL_DIR}/scripts/corpus_db.py rebuild-sentences \
  --db corpus/<author>.db
```

Do not extract, classify, persist, validate, or use `sentence_patterns`. The
only Phase 4 source anchor is a real row in `sentences`, selected at writing
time for a specific planned target sentence.

### 6. Finalize

After all stories are `done`:

```bash
python3 ${HERMES_SKILL_DIR}/scripts/corpus_db.py rebuild-fts --db corpus/<author>.db
python3 ${HERMES_SKILL_DIR}/scripts/corpus_db.py report --db corpus/<author>.db
```

Do not discard `ingestion_log` until the corpus has been manually spot-checked.

When producing reports, remember that the `stories` table has no `status` column. Use `corpus_db.py report`, `corpus_db.py list --status ...`, or a direct query against `ingestion_log`.

## Agent Boundaries

Agents decide:

- story boundaries
- paragraph segmentation
- whether a source section is editorial matter
- whether OCR/mojibake repair is safe
- whether a story is complete enough for `done`

Python tools may only:

- create SQLite schema
- insert/update rows
- count words
- list pending/review items
- read statuses from `ingestion_log`
- rebuild FTS5
- export reports

Do not add regex title detection, EPUB parsing heuristics, PDF layout heuristics, or automatic preface removal to Python.

## Subagent Output Contract

Extraction and cleanup agents must write JSON shaped like:

```json
{
  "story_id": "lovecraft/the-call-of-cthulhu",
  "title": "The Call of Cthulhu",
  "collection": null,
  "source_file": "sources/lovecraft/source.txt",
  "pub_year": 1928,
  "status": "done",
  "confidence": 0.94,
  "reason": "Complete story extracted; editorial intro excluded.",
  "paragraphs": [
    "First paragraph...",
    "Second paragraph..."
  ]
}
```

Use `needs_review` when unsure. A clean `needs_review` with evidence is better than a false `done`.

Validation reports must not introduce alternate status vocabularies. Use only:

```json
{
  "validated_status": "done"
}
```

or:

```json
{
  "validated_status": "needs_review"
}
```

## Common Pitfalls

1. **Letting Python become a parser.** If a decision requires reading judgment, use an agent.
2. **Overloading one subagent.** One extraction target per subagent. Batch according to `delegation.max_concurrent_children`.
3. **Under-specifying context.** Child agents start fresh. Give exact source path, target title, expected output path, and exclusion rules.
4. **Trusting confidence alone.** Low word count, duplicate titles, and missing source references still need review.
5. **Discarding logs too early.** Keep `ingestion_log` and run artifacts until the corpus is spot-checked.

## Verification Checklist

- [ ] `corpus/<author>.db` exists
- [ ] `stories`, `paragraphs`, `paragraphs_fts`, `sentences`, `sentences_fts`, and `ingestion_log` exist
- [ ] every intended story is `done` or intentionally `needs_review`
- [ ] status counts come from `ingestion_log`, not from `stories`
- [ ] no story has `word_count < 300` unless explicitly justified
- [ ] FTS5 rebuild completed
- [ ] each accepted paragraph has sentence rows
- [ ] report output matches expected corpus size
- [ ] at least 3 story samples were compared against source text

## Phase 2 Evidence Hygiene

When deriving author contracts from an approved corpus, every card must keep evidence structured and local to the Phase 1 corpus.

Required shape for card-level `evidence_refs`:

```yaml
evidence_refs:
  - id: "ev-theme-world-rules-001"
    source_work: "author/story-id"
    source_location: "paragraph 12"
    observed_behavior: "What the passage does textually/functionally."
    supports_specific_claim: "The exact card claim this evidence supports."
    relevant_function: "The function this evidence demonstrates."
    not_a_license_for: "What this evidence must not authorize."
```

Rules:

- Do not use string-only `evidence_refs`.
- Do not cite works outside `corpus/<author>.db` as evidence for a run.
- `source_work` must be a `story_id` in the DB, or a clearly named mechanical artifact such as `working/raw_style_profile.json`.
- Do not write `source_work: unknown` or `source_location: unspecified`.
- `observed_behavior` must describe observed textual function; it must not merely repeat `story_id#paragraph`.
- If card evidence is repaired, regenerate both `evidence.notes.yaml` and `working/evidence.candidates.yaml`; do not leave stale candidate evidence.
- If these conditions fail, `absorption.report.yaml` must set `ready_for_phase3: false`.

## Phase 2: Author Pack Construction

Use `references/prompts/run_phase2_author_pack.md` to build `author-models/<author>/` from the approved corpus. Run one card agent per required card whenever runtime concurrency permits.

Required outputs:

```text
author-models/<author>/
  theme.contract.yaml
  style.contract.yaml
  evidence.notes.yaml
  absorption.report.yaml
```

Rules:

- Every card must include use, non-use, rewrite moves, prohibited moves, examples, failure signs, repair moves, and evidence refs.
- `evidence_refs` must be structured objects tied to `corpus/<author>.db`.
- Evidence must include `relevant_function` and `not_a_license_for`.
- Claims without evidence may be hypotheses, but must not become generation rules.

## Phase 3: Artifact Validation & Calibration

Use `references/prompts/run_phase3_validation.md` to validate the author pack before writing.

Required validated outputs:

```text
author-models/<author>/validated/
  theme.contract.yaml
  style.contract.yaml
  evidence.notes.yaml
  instruction.pairs.yaml
  phase3.release.yaml
```

Fase 4 is blocked unless `phase3.release.yaml` has:

```yaml
generation_allowed_for_phase_4: true
```

Phase 3 does not validate pre-extracted sentence patterns. Sentence anchoring is
performed in Phase 4 from real corpus sentences, after a concrete
`sentence_meaning_plan` exists.

## Phase 4: Writing Runtime

Use `references/prompts/run_phase4_writing_runtime.md`. The production method is
**sentence-by-sentence literal source anchoring**. The old
`sentence_patterns`/`structural_pattern_anchor` idea is not a production mode,
not a retrieval layer, and not valid release evidence.

Length is part of form, not an afterthought. A run that chooses a corpus-like
paragraph count but writes paragraphs at flash-fiction density is failed. The
length advisor must compute story word-count percentiles and paragraph
word-density percentiles, then write explicit release floors into
`length.selection.yaml`. For a standard run, use at least corpus p25 story words
as `min_total_words` unless the user explicitly requests shorter output.

Canonical sentence flow:

```text
paragraph_reader_contract
→ paragraph_assertions
→ sentence_meaning_plan with semantic payload, no final prose
→ literal source_sentence_anchor selection from `sentences`
→ source_to_target_alignment_plan
→ target sentence generation
→ independent source_sentence_fidelity_check
→ sentence_sanity_check
→ sentence_anchor_final_repair_pass
→ paragraph audit
→ paragraph release
→ story assembly and story audit
→ Phase 4.5 final text repair gate
→ final release
```

Every final sentence must be a necessary imitation of one selected source sentence's formal machine, with different semantic content. The selected source sentence controls architecture, order of operations, coordination/subordination, contrast, negation, enumeration, delay, closure, and relation between sentence parts. The target content comes only from the blueprint, paragraph plan, neutral paragraph, continuity bible, and user constraints.

Do not use these as production modes:

- `surface_transposition_baseline`: word-swapping a source sentence; allowed only as quarantined experiment.
- generic `structural_pattern_anchor` or `sentence_patterns`: invalid in production.

### Phase 4 Required Artifacts

For each paragraph:

```text
paragraph.request.yaml
neutral.paragraph.yaml
source_sentence_anchor.selection.yaml
paragraph.rewrite.plan.yaml
candidate.output.yaml
sentence_sanity.audit.yaml
sentence_anchor.final_audit.yaml
sentence_anchor.repair.plan.yaml, if needed
repaired.candidate.output.yaml, if needed
final.anchor.lock.yaml
audit.report.yaml
repair.plan.yaml, if needed
final.paragraph.yaml
paragraph.release.yaml
```

`neutral.paragraph.yaml` must be genuine neutral prose. It is invalid to wrap
the final prose in labels such as `Neutral p003 sentence 2:` or other metadata just
to make `candidate.output.yaml` differ mechanically from the neutral draft. If
stripping those labels makes the neutral text equal to the candidate/final
paragraph, regenerate the neutral draft.

At story level:

```text
story.assembly.yaml
story.audit.report.yaml
final.output.yaml
final.text.repair.report.yaml
final.text.repair.plan.yaml, if repair is needed
final.repaired.output.yaml, if repair is needed
final.repair.audit.yaml
final.release.yaml
run.decision.log.yaml
```

`final.output.yaml` must include both `final_text` and paragraph refs. Keeping a legacy `text` alias is allowed, but `final_text` is required for downstream tooling.

### Source Sentence Anchor Selection

`source_sentence_anchor.selection.yaml` must preserve
`source_sentence_anchor_selection`: target `sentence_id`, semantic payload ref,
`selected_source_sentence_ref` with `story_id`/`sentence_id`/positions/hash,
literal `selected_source_sentence_text`, rejected candidate source sentences,
part-by-part alignment plan, and semantic content that must not be copied.

The alignment agent, writer, and independent auditor may read the source sentence
text. The writer must imitate the actual sentence architecture while replacing
the semantic payload. Block if the alignment is generic enough that many
unrelated source sentences could replace the chosen one.

The selector must not walk sequentially through a source work and assign the
next available sentence. For each target sentence, retrieve several candidate
source sentences, record rejected candidates, and explain why the selected
source is necessary for that sentence's semantic payload. A source story
over-concentration or long sequential run is a release blocker unless the user
explicitly requested imitation of one specific source work.

Do not let generic GPT rhetoric pass as source fidelity. A surface formula such
as `not with X, but with Y` is blocked unless the chosen source sentence has an
equivalent contrastive/corrective operation and the alignment cites that
operation explicitly.

### Sentence Anchor Final Repair Pass

Before paragraph release, run
`references/prompts/run_phase4_sentence_anchor_repair_pass.md`. This pass audits every
target/source sentence pair by rhetorical operation, not by punctuation or
sentence length. It must write `sentence_anchor.final_audit.yaml` and
`final.anchor.lock.yaml` for every paragraph.

Only `strong_anchor` and `acceptable_anchor` may appear in
`final.anchor.lock.yaml`. If a sentence is `weak_anchor` or `failed_anchor`, the
runtime must find a better real source sentence and rewrite only that sentence,
preserving the semantic payload. When repair happens, write
`sentence_anchor.repair.plan.yaml` and `repaired.candidate.output.yaml`.

The pass must block shallow matches where the justification is only same length,
same punctuation, same semicolon, or generic "opening / qualification /
implication". The source and target need the same local rhetorical operation:
testimony, public/private contrast, credibility defense, evidence inventory,
epistemic caveat, ominous consequence, documentary enumeration, sensory
observation, inference from material detail, or closing warning.

### Phase 4.5 Final Text Repair Gate

After `story.audit.report.yaml` and `final.output.yaml`, but before
`final.release.yaml`, run `references/prompts/run_phase45_final_text_repair.md`.

This gate is not a beauty pass. It may only repair concrete local findings:

- duplicated phrase or accidental patch artifact;
- unclear agent, antecedent, pronoun, predicate, or transition;
- false-positive repair, such as removing a legitimate negative imperative
  because it was mistaken for the blocked `not X but Y` template;
- residual generic GPT rhetoric not licensed by the selected source sentence;
- weak anchor fit visible only after story assembly;
- continuity glitch introduced during assembly.

Every repair must say whether it preserves the current source sentence anchor or
requires explicit re-anchoring. If it re-anchors, update the relevant paragraph
artifact, sentence mapping, final anchor lock, and final output.

Allowed:

```text
repair one sentence
restore a previous valid sentence
remove accidental duplication
clarify antecedent without changing facts
replace source anchor and regenerate only that sentence
```

Forbidden:

```text
rewrite the whole story
improve style without a concrete finding
change blueprint, causal chain, characters, ending, or symbols
create a new generic ban from one false positive
remove legitimate constructions just because they contain a surface token
```

Required story-level files:

```text
final.text.repair.report.yaml
final.text.repair.plan.yaml, if any repair is required
final.repaired.output.yaml, if any repair is applied
final.repair.audit.yaml
```

`final.release.yaml` must include:

```yaml
approved_output_ref: "final.output.yaml | final.repaired.output.yaml"
final_text_repair_status: "clean | repaired"
final_repair_audit_ref: "final.repair.audit.yaml"
```

Forbidden legacy fields:

```text
sentence.pattern.selection.yaml
sentence_pattern_selection
source_sentence_pattern_id
selected_source_sentence_pattern_id
pattern_structural_match
why_this_pattern_is_necessary
clause_skeleton
structural_signature_used
```

Any occurrence of these fields in Phase 4 artifacts blocks release.

### Candidate Output Contract

Required per output sentence in `candidate.output.yaml`: `sentence_id`,
`output_sentence`, `source_semantic_units`, `source_sentence_ref`,
`source_sentence_text_hash`, `source_to_target_alignment_ref`,
`source_sentence_fidelity`, and `target_semantic_independence`.

Audit must block release if:

- any output sentence lacks `source_sentence_ref`;
- any Phase 4 artifact contains a forbidden legacy pattern field;
- `sentence_anchor.final_audit.yaml` or `final.anchor.lock.yaml` is missing;
- any locked final sentence is still `weak_anchor` or `failed_anchor`;
- `repair_required: true` but no `sentence_anchor.repair.plan.yaml` and `repaired.candidate.output.yaml` exist;
- source anchors are assigned sequentially or overwhelmingly from one source story without local necessity;
- `source_sentence_fidelity`, `target_semantic_independence`, or source-selection reasons are boilerplate repeated across many sentences;
- source sentence selection happened after target sentence generation;
- the selected source sentence is not necessary for that sentence's local function;
- the candidate copies source-sentence content, imagery, conclusion, objects, entities, scene, or memorable phrasing;
- the candidate fails to match the selected source sentence's formal machine;
- the candidate uses a generic rhetorical template not licensed by the selected source sentence;
- punctuation is used as a shallow proxy for fidelity;
- `candidate_text == neutral_text`;
- `declared_transformations` is absent;
- a sentence has category error, unclear agent, unresolved pronoun, broken predicate fit, or copied discourse marker without narrative need.

### Mechanical Validation

After a Phase 4 run, Hermes must execute:

```bash
python3 ${HERMES_SKILL_DIR}/scripts/validate_phase4_run.py \
  --run-dir runs/<author>/<run_id> \
  --paragraph-count <N> \
  --min-total-words <floor_from_length_selection> \
  --min-median-paragraph-words <floor_from_length_selection> \
  --report runs/<author>/<run_id>/mechanical.validation.yaml
```

This script cannot approve literary quality. It only catches structural release errors. If it fails, Hermes must repair the artifacts before presenting final text.
