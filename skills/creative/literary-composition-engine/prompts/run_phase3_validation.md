# Phase 3 Artifact Validation & Calibration

Validate and calibrate author pack artifacts before any writing runtime.

Inputs:

```text
author-models/<author_id>/theme.contract.yaml
author-models/<author_id>/style.contract.yaml
author-models/<author_id>/evidence.notes.yaml
corpus/<author_id>.db
authorial-contract-rulebook.md / architecture.md
```

Outputs:

```text
author-models/<author_id>/phase3-validation/
  validation.manifest.yaml
  card.inventory.yaml
  claim.registry.yaml
  evidence.trace.yaml
  operationality.report.yaml
  anti_pastiche.report.yaml
  contract.conflicts.yaml
  activation.fixtures.yaml
  activation.test.report.yaml
  coverage.report.yaml
  calibration.patch.yaml
  human.review.queue.yaml
  validation.report.yaml
  phase3.release.yaml

author-models/<author_id>/validated/
  theme.contract.yaml
  style.contract.yaml
  evidence.notes.yaml
  instruction.pairs.yaml
  phase3.release.yaml
```

Required checks:

- All 8 cards exist and are executable.
- All generation claims are supported or narrowed.
- Evidence exists in the local corpus and includes `not_a_license_for`.
- No symbol/lexicon/syntax/tone pastiche risk remains as blocker.
- No direct contradiction or scope invasion remains unresolved.
- `instruction.pairs.yaml` can be compiled.
- Do not validate or produce any `sentence_patterns` artifact. Source sentence
  anchors are selected only inside Phase 4, after a concrete
  `sentence_meaning_plan` exists.

Gate values:

```yaml
overall_gate_status: "passed | passed_with_runtime_flags | failed_requires_calibration | failed_requires_human_review"
generation_allowed_for_phase_4: true | false
```

Only write `validated/phase3.release.yaml` with `generation_allowed_for_phase_4: true` if no blockers remain.

Return final gate status, validated path, phase4 flags, and blockers.
