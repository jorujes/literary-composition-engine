# Phase 4 Writing Runtime

Run the complete writing runtime from a validated author pack to final release.

Inputs:

```text
author_id
writing request or user prompt
author-models/<author_id>/validated/
corpus/<author_id>.db
```

Before writing:

1. Load `validated/phase3.release.yaml`.
2. Block if `generation_allowed_for_phase_4` is not `true`.
3. Create `runs/<author_id>/<run_id>/`.
4. Write `run.manifest.yaml`, `author.pack.lock.yaml`, and `writing.request.yaml`.
5. Do not use the author name as a writing shortcut.

Workflow:

1. Interpret request mode:
   - `generate_outline_candidates`
   - `user_premise_to_outlines`
   - `user_outline_to_story`
   - `user_draft_to_authorial_rewrite`
   - `continuation`
   - `isolated_paragraph_or_scene`
2. If outlines are needed, generate contract-compatible outlines and audit them.
3. Suggest length from actual corpus stats; use p25/median/p75 or clusters for story word count, paragraph count, paragraph word density, and sentence density. Do not offer arbitrary short options.
4. After user/driver selection, write `outline.selection.yaml` and `length.selection.yaml`.
5. Build `story.blueprint.yaml` with concrete narrator, action chain, knowledge arc, stakes, symbols, and invention limits.
6. Build `story.progression.plan.yaml` and `paragraph.plan.yaml`.
7. For each paragraph:
   - write `paragraph.request.yaml`;
   - draft `neutral.paragraph.yaml` as plain neutral prose;
   - create `sentence_meaning_plan` with semantic payload only, no final prose;
   - select literal source sentence anchors directly from `sentences`;
   - create `source_to_target_alignment_plan`;
   - write `paragraph.rewrite.plan.yaml`;
   - generate `candidate.output.yaml`;
   - run independent sentence anchor audit using `references/prompts/audit_phase4_sentence_anchor.md`;
   - run the final sentence-anchor repair pass using `references/prompts/run_phase4_sentence_anchor_repair_pass.md`;
   - run paragraph audit;
   - repair/replan until no blockers;
   - write `final.anchor.lock.yaml`;
   - write `final.paragraph.yaml` and `paragraph.release.yaml`;
   - update `continuity.bible.yaml`.
8. Assemble released paragraphs in `story.assembly.yaml` without rewriting them.
9. Audit the story globally in `story.audit.report.yaml`.
10. Write `final.output.yaml` with `final_text`, paragraph refs, provenance, warnings.
11. Run Phase 4.5 final text repair with `references/prompts/run_phase45_final_text_repair.md`.
12. Write `final.release.yaml`, pointing to `final.output.yaml` or `final.repaired.output.yaml`.
13. Run mechanical validation:

```bash
python3 ${HERMES_SKILL_DIR}/scripts/validate_phase4_run.py \
  --run-dir runs/<author_id>/<run_id> \
  --paragraph-count <N> \
  --min-total-words <floor_from_length_selection> \
  --min-median-paragraph-words <floor_from_length_selection> \
  --report runs/<author_id>/<run_id>/mechanical.validation.yaml
```

Neutral draft rule:

`neutral.paragraph.yaml` must contain a real neutral paragraph in plain prose.
It must not be final prose with labels such as `Neutral p003 sentence 2: ...`, a
metadata wrapper, or the final candidate with cosmetic substitutions. If
removing labels from the neutral draft yields the candidate or final paragraph,
the run is invalid and must regenerate the neutral draft.

If mechanical validation fails, repair artifacts and rerun it before returning.

Phase 4.5 final text repair rule:

After `final.output.yaml`, do a story-level pass that reads the assembled text
sentence by sentence. This pass may fix only concrete local defects: accidental
duplication, unclear agent/antecedent, false-positive repair, residual generic
GPT rhetoric, weak anchor after assembly, or continuity glitch. It must not
rewrite the story for taste.

Write:

```text
final.text.repair.report.yaml
final.text.repair.plan.yaml, if repair is needed
final.repaired.output.yaml, if repair is applied
final.repair.audit.yaml
```

Every final repair must declare whether it preserves the existing source
sentence anchor or explicitly re-anchors the affected sentence. A legitimate
negative imperative such as "Do not investigate the bottom..." must not be removed
merely because generic `not X, but Y` templates are blocked; that is a
false-positive repair and should be restored.

Canonical sentence rule:

Every final sentence must be a necessary imitation of one real source sentence
from `corpus/<author>.db:/sentences`, with different semantic content. There is
no `sentence_pattern` layer in production. Do not use pattern ids, skeletons, or
pre-extracted pattern descriptions as the anchor. The anchor is the literal
source sentence itself.

Length rule:

`length.selection.yaml` must include the chosen paragraph count, target total
word range, minimum releasable total words, target median paragraph words, and
minimum releasable median paragraph words. A `standard` run must not use only
median paragraph count. It must also match corpus density. If corpus median is
24 paragraphs and median paragraph length is 128 words, a 24-paragraph story
with 45-word paragraphs is a failed compact run, not a standard run.

Recommended release floors for a standard corpus-compatible run:

```yaml
length_release_gates:
  min_total_words: "at least corpus p25 story word count, unless user explicitly requests shorter"
  target_total_words: "near corpus median story word count"
  min_median_paragraph_words: "at least about 65% of corpus median paragraph words"
  target_median_paragraph_words: "near corpus median paragraph words"
```

Source-anchor selection rule:

Do not assign source anchors sequentially from one story. For every planned
sentence, retrieve multiple candidate source sentences from `sentences_fts` or
direct corpus browsing whose actual sentence form can carry that sentence's
semantic payload, then choose one and record rejected candidates. The selected
source must be necessary enough that replacing it with many unrelated source
sentences would weaken the justification.

Write `source_sentence_anchor.selection.yaml`, never
`sentence.pattern.selection.yaml`. It must include for each planned target
sentence:

```yaml
source_sentence_anchor_selection:
  planned_sentences:
    - sentence_id: ""
      semantic_payload_ref: ""
      target_semantic_job: ""   # semantic plan only, not final prose
      selected_source_sentence_ref:
        story_id: ""
        sentence_id: 0
        paragraph_position: 0
        sentence_position: 0
        source_text_hash: ""
      selected_source_sentence_text: ""
      candidate_source_sentences_considered:
        - source_sentence_ref: {}
          source_sentence_text: ""
          useful_formal_features_in_this_exact_sentence: []
          rejection_reason: ""
      source_sentence_parts:
        - part_id: "src_001"
          source_words_or_span: ""
          formal_job: ""
      target_payload_slots:
        - slot_id: "tgt_001"
          planned_content: ""
          must_fit_source_part: "src_001"
      why_this_exact_sentence_is_necessary: ""
source_to_target_alignment_plan:
  - alignment_ref: ""
    sentence_id: ""
    source_sentence_ref: {}
    source_sentence_text: ""
    target_semantic_job: ""
    source_to_target_part_map:
      - source_words_or_span: ""
        source_formal_job: ""
        target_payload: ""
        target_formal_job: ""
    required_surface_constraints:
      - "what the target sentence must preserve from this exact source sentence form"
    forbidden_surface_escapes:
      - "generic LLM contrast/correction/solemnity not present in the source sentence"
```

Do not use boilerplate such as "reuses the formal operation of the source
sentence" as the reason. The selection reason and part map must be so specific
that the auditor can reject the sentence if a different source sentence would
serve just as well.

The target writer may see `selected_source_sentence_text`, but must not copy its
semantic content, images, scene, entities, conclusion, proper nouns, or memorable
phrasing. The task is to force new semantic payload into the old sentence's
actual architecture.

Final sentence-anchor repair pass:

After `candidate.output.yaml` and the first independent sentence anchor audit,
run `references/prompts/run_phase4_sentence_anchor_repair_pass.md`. This pass must not
restart the story. It audits each final sentence against its selected literal
source sentence and classifies the anchor:

```yaml
anchor_status_values:
  - strong_anchor
  - acceptable_anchor
  - weak_anchor
  - failed_anchor
```

The classification must compare rhetorical operation, not only length,
punctuation, or clause count. Examples of operations:

```yaml
rhetorical_operations:
  - testimonial justification
  - contrast between public explanation and private account
  - negative request followed by correction
  - narrator credibility self-defense
  - evidentiary inventory
  - epistemological qualification
  - ominous consequence
  - documentary enumeration
  - closing warning
```

If a sentence is `weak_anchor` or `failed_anchor`, find a better real source
sentence in `sentences`, rewrite only that target sentence to fit the new source
sentence, and preserve the semantic payload. Do not alter facts, characters,
causal order, knowledge state, or authorized symbols.

Required final pass artifacts per paragraph:

```text
sentence_anchor.final_audit.yaml
final.anchor.lock.yaml
```

Required only when repair was needed:

```text
sentence_anchor.repair.plan.yaml
repaired.candidate.output.yaml
```

`sentence_anchor.final_audit.yaml` must use:

```yaml
sentence_anchor_final_audit:
  paragraph_id: ""
  overall_status: "passed | blocked"
  repair_required: false
  sentence_results:
    - sentence_id: ""
      target_sentence: ""
      selected_source_sentence_ref: {}
      selected_source_sentence_text: ""
      target_rhetorical_operation: ""
      source_rhetorical_operation: ""
      operation_match: "exact | close | partial | no"
      initial_anchor_status: "strong_anchor | acceptable_anchor | weak_anchor | failed_anchor"
      final_anchor_status: "strong_anchor | acceptable_anchor | weak_anchor | failed_anchor"
      why_status: ""
      required_repair: ""
```

`final.anchor.lock.yaml` must use:

```yaml
final_anchor_lock:
  paragraph_id: ""
  overall_status: "locked"
  locked_candidate_ref: "candidate.output.yaml | repaired.candidate.output.yaml"
  final_text_ref: "final.paragraph.yaml"
  repairs_applied: false
  sentence_locks:
    - sentence_id: ""
      final_anchor_status: "strong_anchor | acceptable_anchor"
      final_output_sentence: ""
      source_sentence_ref: {}
      source_sentence_text_hash: ""
      target_rhetorical_operation: ""
      source_rhetorical_operation: ""
      operation_match: "exact | close"
```

Release is blocked if final audit or lock is missing, if any final sentence
remains `weak_anchor`/`failed_anchor`, if `repair_required: true` lacks a repair
plan and repaired candidate, or if the lock points to text that differs from
`final.paragraph.yaml`.

Candidate output contract:

```yaml
sentence_mapping:
  - sentence_id: ""
    output_sentence: ""
    source_semantic_units: []
    source_sentence_ref: {}
    source_sentence_text_hash: ""
    source_to_target_alignment_ref: ""
    source_sentence_fidelity: >
      Explain exactly which source sentence part licensed each major target
      sentence part.
    target_semantic_independence: >
      Explain how source content/images/entities/conclusions were not copied.
```

Forbidden legacy fields:

```yaml
must_not_appear:
  - source_sentence_pattern_id
  - selected_source_sentence_pattern_id
  - sentence_pattern_selection
  - pattern_structural_match
  - why_this_pattern_is_necessary
  - clause_skeleton
  - structural_signature_used
```

If any forbidden legacy field appears, the run is invalid.

Generic rhetorical templates:

Surface moves that models commonly invent, such as `not with X, but with Y`, are
blocked unless the selected source sentence itself has an equivalent contrastive
or corrective machine and the alignment cites that machine explicitly. Do not
add a contrast just because it sounds literary.

Return:

```text
release status
run path
final.output.yaml path
full final text
warnings
mechanical validation status
```
