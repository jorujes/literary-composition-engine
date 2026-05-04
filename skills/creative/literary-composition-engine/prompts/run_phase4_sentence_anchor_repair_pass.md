# Phase 4 Sentence Anchor Final Repair Pass

Run this after `candidate.output.yaml` and the first independent sentence
anchor audit exist, before `final.paragraph.yaml` and `paragraph.release.yaml`
are released.

Goal: ensure every final target sentence is a necessary imitation of one real
source sentence's rhetorical operation, not merely similar in length,
punctuation, or generic "opening / qualification / implication" shape.

Inputs:

```text
paragraph.request.yaml
neutral.paragraph.yaml
sentence_meaning.plan.yaml
source_sentence_anchor.selection.yaml
paragraph.rewrite.plan.yaml
candidate.output.yaml
audit.report.yaml or sentence-anchor audit
continuity.bible.yaml excerpt
corpus/<author_id>.db
```

Outputs:

```text
sentence_anchor.final_audit.yaml
sentence_anchor.repair.plan.yaml, only if repair_required
repaired.candidate.output.yaml, only if repair_required
final.anchor.lock.yaml
```

## 1. Classify Each Anchor

For every sentence mapping, identify:

- target semantic payload;
- target sentence;
- selected literal source sentence;
- target rhetorical operation;
- source rhetorical operation;
- whether the operations match.

Use these status values:

```yaml
anchor_status_values:
  strong_anchor: >
    Source and target execute the same local rhetorical operation, with the
    same kind of sentence movement and no copied source semantics.
  acceptable_anchor: >
    Source licenses the target with a narrow, explicit difference that does not
    weaken mimicry or semantic clarity.
  weak_anchor: >
    Source was selected mainly for length, punctuation, broad clause shape, or
    generic explanation; the rhetorical operation does not really match.
  failed_anchor: >
    Source cannot license the target, target copies source semantics, or target
    becomes semantically broken to fit source form.
```

Useful rhetorical operations include, but are not limited to:

```yaml
rhetorical_operations:
  - "testimonial justification"
  - "contrast between public explanation and private account"
  - "negative request followed by correction"
  - "narrator credibility self-defense"
  - "evidentiary inventory"
  - "epistemological qualification"
  - "ominous consequence"
  - "documentary enumeration"
  - "qualified sensory observation"
  - "chain of evidence"
  - "deduction from material detail"
  - "closing warning"
```

Block shallow approvals. Do not approve because:

- source and target both have commas;
- both are long;
- both have semicolon;
- both contain an introductory phrase;
- a boilerplate explanation says "opening, qualification, implication";
- the source could be replaced by many unrelated corpus sentences.

## 2. Write Final Audit

Always write:

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

`overall_status` can be `passed` only if every `final_anchor_status` is
`strong_anchor` or `acceptable_anchor`.

## 3. Repair Weak Or Failed Anchors

If any sentence is `weak_anchor` or `failed_anchor`:

1. Preserve its semantic payload exactly.
2. Search `sentences` / `sentences_fts` for source sentences whose rhetorical
   operation matches the target operation.
3. Record multiple candidates, including rejected candidates.
4. Select a new literal source sentence.
5. Rewrite only the target sentence to fit the new source sentence.
6. Update sentence mapping, source hash, source alignment, and paragraph text.
7. Do not change story facts, entities, causal order, knowledge state, symbols,
   or user constraints.

Write:

```yaml
sentence_anchor_repair_plan:
  paragraph_id: ""
  repairs:
    - sentence_id: ""
      repair_action: "replace_anchor_and_rewrite_sentence | rewrite_sentence_to_source | split_sentence | block"
      semantic_payload_to_preserve: ""
      required_rhetorical_operation: ""
      old_source_sentence_ref: {}
      old_source_sentence_text: ""
      old_failure_reason: ""
      new_source_candidates:
        - source_sentence_ref: {}
          source_sentence_text: ""
          rhetorical_operation: ""
          fit_reason: ""
          rejection_reason: ""
      selected_new_source_sentence_ref: {}
      selected_new_source_sentence_text: ""
      rewrite_instruction: ""
      forbidden_changes:
        - "do not alter narrative content"
        - "do not insert a new fact"
        - "do not copy semantic content from the source"
```

Then write `repaired.candidate.output.yaml`. It must have the same structure as
`candidate.output.yaml`, with repaired sentences and updated source mappings.

If repair would require changing the story, mark the sentence `failed_anchor`
and block the paragraph.

## 4. Lock Final Anchors

After repair, write:

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

`final.paragraph.yaml` must match the locked candidate text exactly.

## 5. Release Blockers

Block release if:

- `sentence_anchor.final_audit.yaml` is missing;
- `final.anchor.lock.yaml` is missing;
- any `final_anchor_status` is `weak_anchor` or `failed_anchor`;
- `repair_required: true` but no `sentence_anchor.repair.plan.yaml` exists;
- repair was applied but no `repaired.candidate.output.yaml` exists;
- final lock points to a candidate whose text differs from `final.paragraph.yaml`;
- repair changes story content instead of anchor/form;
- source and target operations do not match beyond punctuation or size.
