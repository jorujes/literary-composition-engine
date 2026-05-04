# Blind Phase 4 Sentence Anchor Adversarial Audit

Audit a generated paragraph sentence by sentence. This is a blind adversarial
gate: do not reuse the generator's self-audit, matching status, prior source
analysis, or final lock as evidence.

Inputs:

```text
source literal sentence
target literal sentence
semantic payload for that target sentence
```

The auditor must not receive:

```text
selected_form_match_status
why_selected_before_writing
source_form_analysis from the generator
source_sentence_fidelity from candidate.output.yaml
target_semantic_independence from candidate.output.yaml
final_anchor_status
```

Every sentence starts as:

```yaml
initial_status: "failed_until_demonstrated"
```

For each source/target/payload triple, verify:

1. The target says the planned semantic payload clearly and completely.
2. The target is coherent idiomatic prose in its output language.
3. The source sentence is formally capable of carrying this payload.
4. The target sentence's rhetorical operation matches the source sentence's concrete machinery, not just punctuation, length, broad clause count, or a shared label.
5. The target sentence preserves the selected source sentence's actual architecture:
   - mood or equivalent force;
   - clause count and order;
   - coordination/subordination;
   - rhetorical move;
   - parallelism/repetition;
   - negation/contrast;
   - enumeration shape;
   - opening/closing move;
   - relation between predicates.
6. Punctuation is a consequence of the alignment, not a proxy for approval.
7. No source content, image, scene, conclusion, entity, object, or memorable phrasing was copied.
8. Every agent/pronoun/deictic marker is grounded in the payload or paragraph context.
9. No new content was introduced merely to complete an inherited structure.
10. Any generic rhetorical template in the target, such as `not with X, but with Y`, is licensed by an equivalent contrastive/corrective machine in the selected source sentence.

Do not accept retrojustification. A source sentence that is interrogative cannot
anchor a factual declaration unless the matching artifact proves an equivalent
questioning force in the target. A bodily event sentence cannot anchor an
administrative inventory. A sentence listing objects cannot anchor an event
sequence. These are `blocked_for_replan`, not taste issues.

Semantic sanity is a release gate. Reject targets that are formally clever but
wrong in prose, for example:

- category errors: a room listed among objects in itself;
- bad antecedents;
- translation-like phrases;
- artificial technical vocabulary;
- predicates that do not fit their subject;
- vague abstractions used to fill a source sentence's shape.

If a sentence fails, the next cycle must rewrite the target sentence or replace
the source sentence. Do not improve only the justification.

Findings:

```yaml
blind_anchor_adversarial_audit:
  run_id: ""
  paragraph_id: ""
  cycle_id: ""
  audited_candidate_ref: "candidate.output.yaml"
  auditor_visibility: "source_target_payload_only"
  initial_policy: "all_sentences_failed_until_demonstrated"
  overall_status: "passed | blocked"
  sentence_results:
    - sentence_id: ""
      initial_status: "failed_until_demonstrated"
      source_literal: ""
      target_literal: ""
      semantic_payload: ""
      verdict: "passed | failed"
      semantic_coherence_gate: "passed | failed"
      formal_differences:
        opening: ""
        clause_sequence: ""
        subordination_coordination: ""
        rhetorical_turn: ""
        closing: ""
        punctuation: ""
        length: ""
        movement_category: ""
      concrete_reason: >
        Compare source and target concretely. Mention exact source words and
        exact target words. Do not write yes/no boilerplate.
      required_repair:
        needed: false
        repair_type: "rewrite_target | replace_source | none"
        instruction: ""
```

Block if:

- the audit is not blind;
- source/target/payload literals are missing;
- the explanation is generic or does not cite exact source and target movement;
- source and target differ in mood, clause order, turn logic, or category without a pre-declared acceptable difference;
- the sentence is only superficially authorial by punctuation;
- the sentence loses planned meaning;
- the sentence has category error, unclear agent, broken predicate fit, unresolved pronoun, or copied discourse marker without narrative need.
- the target uses a familiar LLM contrast/correction formula that is not present as a formal operation in the selected source sentence.
- the source and target share only punctuation, sentence length, or broad clause count but not the same rhetorical operation.
