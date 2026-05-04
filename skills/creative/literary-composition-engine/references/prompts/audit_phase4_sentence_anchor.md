# Independent Phase 4 Sentence Anchor Audit

Audit a generated paragraph sentence by sentence. This is an independent gate:
do not reuse the generator's self-audit as evidence.

Inputs:

```text
paragraph.request.yaml
neutral.paragraph.yaml
source_sentence_anchor.selection.yaml
sentence_anchor.matching.yaml
paragraph.rewrite.plan.yaml
candidate.output.yaml
continuity.bible.yaml excerpt
corpus/<author_id>.db
```

For each sentence, verify:

1. The sentence meaning plan existed before source selection and did not contain the final sentence.
2. A real source sentence was selected by `story_id`, `sentence_id`, position, `source_text_hash`, and literal `selected_source_sentence_text`.
3. `sentence_anchor.matching.yaml` was written before generation and selected this source as `strong_form_match` or `acceptable_form_match`.
4. The selected source sentence is necessary for this target sentence's semantic job and formal requirements.
5. The target sentence's rhetorical operation matches the source sentence's concrete machinery, not just punctuation, length, broad clause count, or a shared label.
6. `source_to_target_alignment_plan` maps parts of the literal source sentence to parts of the target sentence with sentence-specific detail.
7. The target sentence preserves the selected source sentence's actual architecture:
   - mood or equivalent force;
   - clause count and order;
   - coordination/subordination;
   - rhetorical move;
   - parallelism/repetition;
   - negation/contrast;
   - enumeration shape;
   - opening/closing move;
   - relation between predicates.
8. Punctuation is a consequence of the alignment, not a proxy for approval.
9. No source content, image, scene, conclusion, entity, object, or memorable phrasing was copied.
10. Every agent/pronoun/deictic marker is grounded in the paragraph, blueprint, or continuity.
11. The target sentence still says the planned meaning clearly.
12. No new content was introduced to complete an inherited structure.
13. Any generic rhetorical template in the target, such as `not with X, but with Y`, is licensed by an equivalent contrastive/corrective machine in the selected source sentence and cited in the alignment.
14. The selected anchors are not assigned sequentially from one source work as a convenience. If several consecutive anchors come from the same story, each one must have a local necessity rationale and rejected alternatives.
15. No legacy `sentence_pattern` fields appear anywhere in the paragraph artifacts.

Do not accept retrojustification. A source sentence that is interrogative cannot
anchor a factual declaration unless the matching artifact proves an equivalent
questioning force in the target. A bodily event sentence cannot anchor an
administrative inventory. A sentence listing objects cannot anchor an event
sequence. These are `blocked_for_replan`, not taste issues.

Generic spans are blockers. Reject `source_words_or_span` values like "opening
syntax", "main clause", "clause skeleton", "qualification", or "development"
unless the artifact also cites literal source words and explains their local
sentence job.

Findings:

```yaml
sentence_anchor_audit:
  overall_status: "passed | needs_repair | blocked_for_replan"
  sentence_results:
    - sentence_id: ""
      status: "passed | needs_repair | blocked_for_replan"
      selected_source_is_necessary: "yes | no"
      matching_artifact_check: "passed | missing | failed"
      prewriting_form_match_status: "strong_form_match | acceptable_form_match | weak_form_match | failed_form_match | missing"
      rejected_candidate_check: ""
      source_sentence_fidelity: ""
      target_rhetorical_operation: ""
      source_rhetorical_operation: ""
      operation_match: "exact | close | partial | no"
      formal_match_checks:
        mood_match: "yes | acceptable_difference | no"
        clause_sequence_match: "yes | acceptable_difference | no"
        coordination_subordination_match: "yes | acceptable_difference | no"
        turn_logic_match: "yes | acceptable_difference | no"
        punctuation_function_match: "yes | acceptable_difference | no"
        category_fit: "yes | acceptable_difference | no"
      semantic_sanity: ""
      overcopy_check: ""
      generic_template_check: ""
      required_repair: ""
```

Block if:

- source selection is generic or interchangeable;
- pre-writing `sentence_anchor.matching.yaml` is missing or does not select a strong/acceptable form match;
- alignment is boilerplate;
- source and target differ in mood, clause order, turn logic, or category without a pre-declared acceptable difference;
- the paragraph uses `sentence.pattern.selection.yaml`, `source_sentence_pattern_id`, `pattern_structural_match`, `why_this_pattern_is_necessary`, `clause_skeleton`, or any other `sentence_pattern` field;
- the selected source sentence was chosen only because it was next in sequence;
- the sentence is only superficially authorial by punctuation;
- the sentence loses planned meaning;
- the sentence has category error, unclear agent, broken predicate fit, unresolved pronoun, or copied discourse marker without narrative need.
- the target uses a familiar LLM contrast/correction formula that is not present as a formal operation in the selected source sentence.
- the source and target share only punctuation, sentence length, or broad clause count but not the same rhetorical operation.
