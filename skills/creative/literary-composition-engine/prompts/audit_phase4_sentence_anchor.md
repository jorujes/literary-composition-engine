# Independent Phase 4 Sentence Anchor Audit

Audit a generated paragraph sentence by sentence. This is an independent gate:
do not reuse the generator's self-audit as evidence.

Inputs:

```text
paragraph.request.yaml
neutral.paragraph.yaml
source_sentence_anchor.selection.yaml
paragraph.rewrite.plan.yaml
candidate.output.yaml
continuity.bible.yaml excerpt
corpus/<author_id>.db
```

For each sentence, verify:

1. The sentence meaning plan existed before source selection and did not contain the final sentence.
2. A real source sentence was selected by `story_id`, `sentence_id`, position, `source_text_hash`, and literal `selected_source_sentence_text`.
3. The selected source sentence is necessary for this target sentence's semantic job.
4. The target sentence's rhetorical operation matches the source sentence's rhetorical operation, not just punctuation, length, or broad clause count.
5. `source_to_target_alignment_plan` maps parts of the literal source sentence to parts of the target sentence with sentence-specific detail.
6. The target sentence preserves the selected source sentence's actual architecture:
   - clause count and order;
   - coordination/subordination;
   - rhetorical move;
   - parallelism/repetition;
   - negation/contrast;
   - enumeration shape;
   - opening/closing move;
   - relation between predicates.
7. Punctuation is a consequence of the alignment, not a proxy for approval.
8. No source content, image, scene, conclusion, entity, object, or memorable phrasing was copied.
9. Every agent/pronoun/deictic marker is grounded in the paragraph, blueprint, or continuity.
10. The target sentence still says the planned meaning clearly.
11. No new content was introduced to complete an inherited structure.
12. Any generic rhetorical template in the target, such as `não com X, mas com Y`, is licensed by an equivalent contrastive/corrective machine in the selected source sentence and cited in the alignment.
13. The selected anchors are not assigned sequentially from one source work as a convenience. If several consecutive anchors come from the same story, each one must have a local necessity rationale and rejected alternatives.
14. No legacy `sentence_pattern` fields appear anywhere in the paragraph artifacts.

Findings:

```yaml
sentence_anchor_audit:
  overall_status: "passed | needs_repair | blocked_for_replan"
  sentence_results:
    - sentence_id: ""
      status: "passed | needs_repair | blocked_for_replan"
      selected_source_is_necessary: "yes | no"
      rejected_candidate_check: ""
      source_sentence_fidelity: ""
      target_rhetorical_operation: ""
      source_rhetorical_operation: ""
      operation_match: "exact | close | partial | no"
      semantic_sanity: ""
      overcopy_check: ""
      generic_template_check: ""
      required_repair: ""
```

Block if:

- source selection is generic or interchangeable;
- alignment is boilerplate;
- the paragraph uses `sentence.pattern.selection.yaml`, `source_sentence_pattern_id`, `pattern_structural_match`, `why_this_pattern_is_necessary`, `clause_skeleton`, or any other `sentence_pattern` field;
- the selected source sentence was chosen only because it was next in sequence;
- the sentence is only "Borgesian" by punctuation;
- the sentence loses planned meaning;
- the sentence has category error, unclear agent, broken predicate fit, unresolved pronoun, or copied discourse marker without narrative need.
- the target uses a familiar LLM contrast/correction formula that is not present as a formal operation in the selected source sentence.
- the source and target share only punctuation, sentence length, or broad clause count but not the same rhetorical operation.
