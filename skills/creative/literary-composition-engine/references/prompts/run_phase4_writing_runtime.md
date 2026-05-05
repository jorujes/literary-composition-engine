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
   - run paragraph-local sentence-anchor cycles under `anchor_cycles/cycle_XX/`;
   - copy the approved cycle's `sentence_meaning_plan.yaml` to the paragraph root as `sentence.plan.yaml`;
   - copy the approved cycle's `sentence_anchor.matching.yaml`, `source_sentence_anchor.selection.yaml`, `candidate.output.yaml`, and `blind_anchor_adversarial_audit.yaml` to the paragraph root;
   - write `anchor.cycle.summary.yaml`;
   - write `paragraph.rewrite.plan.yaml`;
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

YAML serialization is a release precondition, not a cleanup task. Before writing
any YAML artifact, prefer block mappings over inline/flow mappings for
text-rich records. Write all full sentences, source quotations, target
sentences, explanations, semantic payloads, `why_*` fields, `reason_*` fields,
and fields containing `:`, quotes, apostrophes, semicolons, brackets, or
comma-heavy prose as block scalars. Use `>-` for single-paragraph prose and
`|-` for text where line breaks or paragraph breaks must be preserved.
`final_text` and `assembled_text` must use `|-`, not `>`, so the validator can
count paragraphs after parsing. Do not use inline maps for candidate source
sentences, source sentence parts, final audit results, or alignment plans. If a
field is conceptually `"yes"` or `"no"`, quote it, or use `true`/`false` only
where the schema explicitly expects a boolean.

Paragraph-local anchor cycle rule:

Do not release a paragraph after a single generator self-check. Each paragraph
must pass a local cycle:

```text
sentence_meaning_plan
-> sentence_anchor.matching
-> source_sentence_anchor.selection
-> candidate.output
-> blind_anchor_adversarial_audit
-> repair failed sentences or approve cycle
```

Write cycle artifacts first under:

```text
paragraphs/<pid>/anchor_cycles/cycle_01/
  sentence_meaning_plan.yaml
  sentence_anchor.matching.yaml
  source_sentence_anchor.selection.yaml
  candidate.output.yaml
  blind_anchor_adversarial_audit.yaml
```

If the blind audit rejects any sentence, create `cycle_02`, then `cycle_03`, up
to `max_cycles_allowed` in `anchor.cycle.summary.yaml`. Do not repair a failed
sentence by improving the explanation. The only allowed repairs are:

```yaml
failed_sentence_repairs:
  - "rewrite target sentence while preserving semantic payload"
  - "replace source sentence with a better literal corpus sentence"
  - "block paragraph and request replan if no source can carry the payload"
```

After a cycle passes, copy the approved cycle files to the paragraph root using
the standard root artifact names. Copy `sentence_meaning_plan.yaml` as
`sentence.plan.yaml`; do not leave the paragraph root without `sentence.plan.yaml`.
The validator reads the root files, and `anchor.cycle.summary.yaml` records
which cycle was approved.

Blind adversarial audit rule:

`blind_anchor_adversarial_audit.yaml` is mandatory before `sentence_anchor.final_audit.yaml`.
The auditor receives only:

```text
source literal sentence
target literal sentence
semantic payload
```

The auditor must not see or rely on:

```text
selected_form_match_status
why_selected_before_writing
source_form_analysis from the generator
final_anchor_status
prior self-audits
```

Every sentence begins as:

```yaml
initial_status: "failed_until_demonstrated"
```

To pass, the audit must compare concrete source and target form:

```yaml
formal_differences:
  opening: ""
  clause_sequence: ""
  subordination_coordination: ""
  rhetorical_turn: ""
  closing: ""
  punctuation: ""
  length: ""
  movement_category: ""
semantic_coherence_gate: "passed | failed"
```

The audit must fail a sentence if the target is semantically incoherent,
idiomatically broken, translation-like, or locally artificial, even when the
formal anchor seems close.

Release blockers for every paragraph:

```yaml
paragraph_anchor_cycle_blockers:
  - "anchor.cycle.summary.yaml missing"
  - "blind_anchor_adversarial_audit.yaml missing or not blind"
  - "candidate too similar to neutral paragraph"
  - "exact final sentence repeated in prior released text"
  - "source sentence too short or formally mismatched for target"
  - "fragmentary semantic payload"
  - "boilerplate sentence such as Anotei o fato / Hoje ao rever / A prudência mandaria when not locally necessary"
  - "repair only changes justification instead of target/source"
```

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

Source-anchor matching and selection rule:

Artifact authorship rule:

Agents must make and write literary decisions directly. Python, shell heredocs,
and generated scripts must not create or hard-code final prose, source sentence
choices, source/target matching reasons, semantic cargo exclusions,
candidate outputs, final paragraphs, or anchor audit judgments. Mechanical
tools may query SQLite, count, validate, copy approved cycle artifacts, and
assemble already released paragraphs. If any script writes literary decision
content, stop the run, set release to blocked, and restart from the affected
stage.

Do not put unreleased target prose inside Python or shell code to count words,
compare length, or check punctuation. If target prose is not yet in a
stage-correct YAML artifact, mechanical tools must not see it.

Write `run.decision.log.yaml` at the run root before final release. It must
record every mechanical tool/script used and explicitly declare that final
prose, anchor selection, matching, semantic exclusions, and audits were created
by agent reasoning, not code generation.
It must also declare:

```yaml
parent_or_driver_preselected_source_anchors: false
delegate_context_included_selected_source_anchors: false
```

Do not assign source anchors sequentially from one story. For every planned
sentence, retrieve multiple candidate source sentences from `sentences_fts` or
direct corpus browsing whose actual sentence form can carry that sentence's
semantic payload, then choose one and record rejected candidates. The selected
source must be necessary enough that replacing it with many unrelated source
sentences would weaken the justification.

Do not preselect or recommend source anchors before the paragraph's
`sentence.plan.yaml` exists on disk. Do not make a parent planning pass that
hands a worker a list of selected source sentence ids. If you use `delegate_task`,
the delegated agent must receive only the run constraints, corpus path,
validated author pack path, and story/paragraph duties; it must create
`sentence.plan.yaml` first and then select anchors inside the paragraph artifact
sequence. Passing "selected anchors recommended" or "use these source ids" to a
worker is after-the-fact laundering and blocks the run.

Before writing `source_sentence_anchor.selection.yaml`, write
`sentence_anchor.matching.yaml`. This file must be created before any final
target sentence exists. It prevents the model from choosing a random source
sentence and retrojustifying it after generation.

Stage order is a mechanical release gate. For each paragraph, write artifacts
in this order:

```text
sentence.plan.yaml
sentence_anchor.matching.yaml
source_sentence_anchor.selection.yaml
paragraph.rewrite.plan.yaml
candidate.output.yaml
blind_anchor_adversarial_audit.yaml
anchor.cycle.summary.yaml
sentence_anchor.final_audit.yaml
final.anchor.lock.yaml
audit.report.yaml
final.paragraph.yaml
paragraph.release.yaml
```

Do not batch-write these in parallel. A paragraph fails if `candidate.output`
or `final.paragraph` predates matching, selection, audit, or lock artifacts.
It also fails if `anchor.cycle.summary.yaml` says a cycle passed before the
matching, selection, candidate, and blind audit files exist.

`sentence.plan.yaml` must be operational. Every sentence item must include:

```yaml
sentence_id: ""
semantic_payload: ""
must_say:
  - ""
must_not_say:
  - ""
required_narrative_action: ""
```

`audit.report.yaml` may not be an empty pass. If it says `overall_status:
passed`, it must include concrete sections for semantic preservation,
continuity, theme, style, symbolic policy, anti-pastiche, slop, Phase 4 flags,
and sentence-plan execution.

For every planned target sentence, first define formal requirements from the
semantic payload. Then retrieve and record at least five candidate source
sentences when the corpus has enough candidates; fewer candidates are allowed
only if the artifact states the corpus search was exhausted for that sentence.

```yaml
sentence_anchor_matching:
  paragraph_id: ""
  written_before_candidate_output: true
  written_before_source_sentence_anchor_selection: true
  sentences:
    - sentence_id: ""
      semantic_payload_ref: ""
      target_semantic_job: ""
      target_form_requirements:
        required_mood: "declarative | interrogative | imperative | fragment_allowed"
        required_clause_sequence:
          - "concrete description of required clause/move in order"
        required_coordination_or_subordination:
          - ""
        required_turn_logic: ""
        required_enumeration_or_contrast: ""
        required_punctuation_function: ""
        required_category_of_movement: ""
        required_narrative_action_type: ""
        required_entity_action_roles:
          - "who/what acts, observes, records, resists, lists, discovers, receives, etc."
        required_discourse_function: ""
        forbidden_action_mismatches:
          - "expedition logistics when target requires ecclesiastical routine"
          - "social illness/reception when target requires clerical evidentiary status"
      incompatible_source_forms:
        - "yes/no question when target must be factual declaration"
        - "bodily crisis event when target must be inventory or assignment"
      candidate_source_sentences:
        # record at least five candidates when the corpus has enough options
        - source_sentence_ref: {}
          source_sentence_text: ""
          source_form_analysis:
            mood: ""
            clause_sequence:
              - ""
            coordination_or_subordination:
              - ""
            turn_logic: ""
            punctuation_function: ""
            category_of_movement: ""
            source_narrative_action_type: ""
            source_entity_action_roles:
              - ""
            source_discourse_function: ""
          narrative_action_match: "exact | close | loose | mismatch"
          entity_action_role_match: "exact | close | loose | mismatch"
          why_action_match_is_not_loose_analogy: ""
          form_match_status: "strong_form_match | acceptable_form_match | weak_form_match | failed_form_match"
          fit_reason_before_writing: ""
          mismatch_reason: ""
      selected_source_sentence_ref: {}
      selected_source_sentence_text: ""
      selected_form_match_status: "strong_form_match | acceptable_form_match"
      narrative_action_match: "exact | close"
      entity_action_role_match: "exact | close"
      why_action_match_is_not_loose_analogy: ""
      acceptable_differences:
        - ""
      why_selected_before_writing: ""
```

`acceptable_form_match` is allowed because perfect matches may not exist, but it
must preserve most governing machinery: mood or equivalent force, clause order,
coordination/subordination, turn logic, category of movement, and punctuation
function where relevant. A merely broad label such as `causal qualification` or
`evidentiary inventory` is not enough.

Action fit is mandatory, not decorative. Before search, name the concrete
target action: e.g. "a narrator records an evidentiary document", "a clerk
physically leads another man into a chapel", "objects are inventoried as proof",
"a hypothesis fails to explain a physical anomaly". A source can pass only if
its literal sentence performs the same or very close action with comparable
entity roles. Do not anchor ecclesiastical routine to expedition logistics just
because both have "after X, someone goes somewhere"; do not anchor an arbitrary
clerical filler to a source about illness, hospitality, or social reaction just
because both can contain a named person.

Semicolons are source-bound. Do not add `;` to a target sentence unless the
selected source sentence also has `;`; never use more semicolons than the
source. If the source has no semicolon, a target semicolon is generic model
style and fails source fidelity.

`strong_form_match` is narrow. Do not mark an anchor strong if the source and
target differ sharply in sentence length, discourse mode, dialect/register,
question/declaration force, object/action category, or sequence of movement.
Use `acceptable_form_match` only when the difference is explicit, local, and
still leaves the source sentence as a necessary machine. If the same target
could be retrojustified from many unrelated sentences, the source is weak.

Block before writing if the best source candidate is only `weak_form_match` or
`failed_form_match`. Search more. A selected question cannot anchor a factual
declaration; a crisis-event sentence cannot anchor an administrative inventory;
a temporal reaction sentence cannot anchor an object list, unless the matching
artifact proves that the same sentence machinery survives and states the narrow
difference.

Write `source_sentence_anchor.selection.yaml`, never
`sentence.pattern.selection.yaml`. It must include for each planned target
sentence:

```yaml
source_sentence_anchor_selection:
  planned_sentences:
    - sentence_id: ""
      semantic_payload_ref: ""
      target_semantic_job: ""   # semantic plan only, not final prose
      matching_ref: "sentence_anchor.matching.yaml#..."
      selected_form_match_status: "strong_form_match | acceptable_form_match"
      target_form_requirements: {}
      selected_source_form_analysis: {}
      narrative_action_match: "exact | close"
      entity_action_role_match: "exact | close"
      why_action_match_is_not_loose_analogy: ""
      acceptable_differences_from_source_form: []
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
          narrative_action_match: "exact | close | loose | mismatch"
          entity_action_role_match: "exact | close | loose | mismatch"
          form_match_status: "strong_form_match | acceptable_form_match | weak_form_match | failed_form_match"
          rejection_reason: ""
      source_sentence_parts:
        - part_id: "src_001"
          source_words_or_span: "" # literal span from the source, never "opening syntax"
          formal_job: ""
          semantic_cargo_to_exclude:
            - source_phrase: ""
              why_excluded: "semantic content in this exact source span, not formal machinery"
              target_language_forbidden_calques:
                - ""
      source_semantic_content_to_exclude:
        - source_phrase: ""
          why_excluded: "semantic content/image/entity from the source, not formal machinery"
          target_language_forbidden_calques:
            - ""
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
        source_semantic_cargo_not_to_copy:
          - ""
    required_surface_constraints:
      - "what the target sentence must preserve from this exact source sentence form"
    forbidden_surface_escapes:
      - "generic LLM contrast/correction/solemnity not present in the source sentence"
```

Do not use boilerplate such as "reuses the formal operation of the source
sentence" as the reason. The selection reason and part map must be so specific
that the auditor can reject the sentence if a different source sentence would
fit just as well. `why_selected_before_writing` and
`why_this_exact_sentence_is_necessary` must cite literal words from the selected
source sentence, and `source_sentence_parts.source_words_or_span` must be an
actual contiguous span from that source sentence, never a label such as
"opening", "main clause", "qualification", or "turning phrase".

Every selected source sentence must also declare
`source_semantic_content_to_exclude`: concrete source images, entities,
conceptual conclusions, and memorable phrases that the target must not inherit,
plus target-language forbidden calques. Formal imitation is allowed; source
semantic cargo is not. For example, if the source contains "black seas of
infinity", a pt-BR target must not contain "mares negros de infinito", and if
the source contains "small drops of water that torturers let fall", the target
must not reuse drops, torturers, or the same torture image.

This exclusion must also happen per source part. If the formal span is "The
Pequots, enfeebled by a previous war", the target may inherit an opening
dependent pressure, but it must not translate "enfeebled" into "enfraquecidos"
or invent an analogous weakening unless the planned payload independently
requires weakening. Each `source_sentence_parts` item must list the semantic
cargo inside that span and the target-language calques that would reveal it was
copied.

Do not use generic source spans such as "opening syntax", "clause skeleton",
"main clause", or "qualification" unless they are accompanied by literal source
words and a sentence-local job. The auditor must be able to point to the exact
words in the source sentence that the target is imitating.

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

The classification must compare concrete source machinery, not only length,
punctuation, clause count, or operation labels. Operation labels must be derived
from the selected source sentence itself, not reused as defaults. Examples of
possible labels:

```yaml
rhetorical_operations:
  - causal qualification
  - contrastive correction
  - evidentiary inventory
  - sensory observation
  - inference from material detail
  - definition by negation
  - temporal reversal
  - catalog followed by conclusion
  - closing constraint
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
      narrative_action_match: "exact | close | loose | mismatch"
      entity_action_role_match: "exact | close | loose | mismatch"
      why_action_match_is_not_loose_analogy: ""
      formal_match_checks:
        mood_match: "'yes' | acceptable_difference | 'no'"
        clause_sequence_match: "'yes' | acceptable_difference | 'no'"
        coordination_subordination_match: "'yes' | acceptable_difference | 'no'"
        turn_logic_match: "'yes' | acceptable_difference | 'no'"
        punctuation_function_match: "'yes' | acceptable_difference | 'no'"
        category_fit: "'yes' | acceptable_difference | 'no'"
        acceptable_differences_from_matching:
          - ""
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
      narrative_action_match: "exact | close"
      entity_action_role_match: "exact | close"
      why_action_match_is_not_loose_analogy: ""
      formal_match_status: "strong_form_match | acceptable_form_match"
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
