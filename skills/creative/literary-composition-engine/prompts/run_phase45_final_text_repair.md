# Phase 4.5 Final Text Repair

Run this after `story.audit.report.yaml` and `final.output.yaml`, before
`final.release.yaml`.

Goal: catch and repair local final-text defects that survive paragraph-level
release, without turning the pass into free rewriting or taste-based polishing.

Inputs:

```text
final.output.yaml
story.assembly.yaml
story.audit.report.yaml
paragraphs/*/final.paragraph.yaml
paragraphs/*/final.anchor.lock.yaml
paragraphs/*/source_sentence_anchor.selection.yaml
paragraphs/*/candidate.output.yaml or repaired.candidate.output.yaml
continuity.bible.yaml
story.blueprint.yaml
```

Outputs:

```text
final.text.repair.report.yaml
final.text.repair.plan.yaml, only if repair_required
final.repaired.output.yaml, only if repair_applied
final.repair.audit.yaml
```

## 1. Read The Assembled Text

Inspect `final.output.yaml#/final_text` sentence by sentence.

Do not judge whether the story could be prettier. Only look for concrete
release defects:

```yaml
final_text_repair_checks:
  - duplicated_or_self_contradictory_phrase
  - unclear_agent_or_antecedent
  - broken_predicate_fit
  - local_semantic_incoherence
  - false_positive_repair
  - residual_generic_gpt_rhetoric
  - continuity_glitch_after_assembly
  - weak_anchor_fit_after_assembly
  - unplanned_new_content
```

## 2. False-Positive Repair Rule

Do not create generic bans from surface tokens.

The blocked pattern is a generic corrective contrast like:

```text
não com X, mas com Y
não era X, mas Y
não por X, mas por Y
```

A simple negative imperative is not that pattern.

Example:

```text
Não investigue o fundo quando a água parecer imóvel contra o vento.
```

This is a legitimate warning/prohibition and must not be changed merely because
it starts with `Não`.

If a previous repair changed a legitimate construction because of a false
positive, restore it and record `finding_type: false_positive_repair`.

## 3. Write Repair Report

Always write:

```yaml
final_text_repair_report:
  run_id: ""
  source_output_ref: "final.output.yaml"
  overall_finding: "clean | repair_required | blocked"
  findings:
    - finding_id: "final-repair-001"
      location:
        paragraph_id: ""
        sentence_id: ""
        text_span: ""
      finding_type: "grammar_or_duplication | semantic_clarity | false_positive_repair | local_gptism | weak_anchor_fit_after_assembly | continuity"
      problem: ""
      why_it_matters: ""
      required_action: "no_change | repair_preserving_anchor | restore_previous_text | reanchor_sentence | block"
      anchor_policy:
        current_anchor_can_be_preserved: true
        reanchor_required: false
        reason: ""
```

If no repair is needed, set:

```yaml
overall_finding: "clean"
findings: []
```

## 4. Allowed Repairs

Allowed:

```yaml
allowed_final_repairs:
  - repair one sentence
  - restore a previous valid sentence
  - remove accidental duplication
  - clarify agent, antecedent, pronoun, or predicate without changing facts
  - repair local GPTism only when it is not licensed by the selected source sentence
  - replace source anchor and regenerate only that sentence
```

Forbidden:

```yaml
forbidden_final_repairs:
  - rewrite the whole story
  - improve style without a concrete finding
  - alter blueprint, causal chain, characters, ending, or symbols
  - insert a new scene, symbol, fact, or explanation
  - remove a legitimate construction because it contains a surface token
  - replace source-anchor fidelity with taste
```

## 5. Write Repair Plan

If repair is required, write:

```yaml
final_text_repair_plan:
  run_id: ""
  repairs:
    - repair_id: "final-repair-001"
      finding_ref: "final.text.repair.report.yaml#final-repair-001"
      target:
        paragraph_id: ""
        sentence_id: ""
      repair_action: "repair_preserving_anchor | restore_previous_text | reanchor_sentence | block"
      original_sentence: ""
      repaired_sentence: ""
      semantic_content_to_preserve:
        - ""
      forbidden_changes:
        - "do not alter story fact"
        - "do not insert new content"
        - "do not alter causal chain"
      anchor_handling:
        preserve_existing_source_sentence_ref: true
        old_source_sentence_ref: {}
        new_source_sentence_ref: {}
        new_source_sentence_text: ""
        source_to_target_alignment_update: ""
```

## 6. Apply Repairs

If repairs are applied:

1. Write `final.repaired.output.yaml`.
2. Preserve all paragraph refs and provenance.
3. Update only the affected sentence(s).
4. If re-anchoring is required, update the relevant paragraph artifacts:
   `source_sentence_anchor.selection.yaml`, `candidate.output.yaml` or
   `repaired.candidate.output.yaml`, `sentence_anchor.final_audit.yaml`, and
   `final.anchor.lock.yaml`.

If no repairs are applied, do not write `final.repaired.output.yaml`.

## 7. Audit Final Repair

Always write:

```yaml
final_repair_audit:
  run_id: ""
  audited_output_ref: "final.output.yaml | final.repaired.output.yaml"
  overall_status: "passed | blocked"
  repairs_checked:
    - repair_id: ""
      semantic_preservation: "passed | failed"
      anchor_integrity: "preserved | reanchored | failed"
      no_new_content: "passed | failed"
      local_issue_resolved: "yes | no"
  release_allowed: true
  blockers: []
```

Release is allowed only if `overall_status: passed` and `release_allowed: true`.

## 8. Release Handoff

After this pass, `final.release.yaml` must point at the approved output:

```yaml
approved_output_ref: "final.output.yaml | final.repaired.output.yaml"
final_text_repair_status: "clean | repaired"
final_repair_audit_ref: "final.repair.audit.yaml"
```

