# Artifact Schemas

This reference describes where runtime artifacts belong and which files are
expected at each phase. These are generated outside the skill directory in the
user's active workspace.

The skill directory contains only reusable instructions, prompts, and scripts.
Do not write corpus databases, author packs, validation reports, or run outputs
inside the skill.

Before creating any generated artifact, load the closest matching contract
schema from `references/schemas/`. Schema files define required structure,
allowed status values, and explicit `must_not` constraints. They are not scoring
rubrics and must not be expanded with arbitrary numeric style controls.

## Workspace Layout

```text
sources/<author>/                         # raw user-provided source files
corpus/<author>.db                        # Phase 1 SQLite corpus database
author-models/<author>/                   # Phase 2/3 author pack artifacts
runs/<author>/<run_id>/                   # Phase 4 writing runs
```

## Phase 1 Corpus Artifacts

```text
corpus/<author>.db
runs/<author>/<run_id>/manifest.json
runs/<author>/<run_id>/extracted/<story_id>.json
runs/<author>/<run_id>/cleanup/<story_id>.json
runs/<author>/<run_id>/validation/<story_id>.yaml
```

Schemas:

```text
references/schemas/phase1/manifest.schema.yaml
references/schemas/phase1/extracted-story.schema.yaml
references/schemas/phase1/validation-report.schema.yaml
```

The SQLite database stores accepted stories, paragraphs, sentences,
full-text-search tables, and ingestion status. LLM agents decide story
boundaries and cleanup. Python persists accepted decisions.

## Phase 2 Author Pack Artifacts

```text
author-models/<author>/
  theme.contract.yaml
  style.contract.yaml
  evidence.notes.yaml
  instruction.pairs.yaml
  absorption.report.yaml
  working/
    raw_style_profile.json
    evidence.candidates.yaml
    cards/*.card.yaml
```

Schemas:

```text
references/schemas/phase2/card.schema.yaml
references/schemas/phase2/theme-contract.schema.yaml
references/schemas/phase2/style-contract.schema.yaml
references/schemas/phase2/evidence-notes.schema.yaml
references/schemas/phase2/instruction-pairs.schema.yaml
```

Contracts and evidence are persistent generated artifacts, not bundled skill
files. They are author-specific and must remain outside the skill.

## Phase 3 Validation Artifacts

```text
author-models/<author>/phase3-validation/
  validation.manifest.yaml
  card.inventory.yaml
  structural.findings.yaml
  claim.registry.yaml
  evidence.trace.yaml
  evidence.findings.yaml
  generalization.findings.yaml
  operationality.report.yaml
  instruction.pairs.yaml
  anti_pastiche.report.yaml
  contract.conflicts.yaml
  activation.fixtures.yaml
  activation.test.report.yaml
  coverage.report.yaml
  calibration.patch.yaml
  human.review.queue.yaml
  validation.report.yaml
  phase3.release.yaml

author-models/<author>/validated/
  theme.contract.yaml
  style.contract.yaml
  evidence.notes.yaml
  instruction.pairs.yaml
  phase3.release.yaml
```

Schemas:

```text
references/schemas/phase3/validation-manifest.schema.yaml
references/schemas/phase3/claim-registry.schema.yaml
references/schemas/phase3/evidence-trace.schema.yaml
references/schemas/phase3/validation-report.schema.yaml
references/schemas/phase3/phase3-release.schema.yaml
```

Phase 4 is blocked unless the validated release artifact explicitly allows
generation.

## Phase 4 Writing Runtime Artifacts

```text
runs/<author>/<run_id>/
  run.manifest.yaml
  author.pack.lock.yaml
  writing.request.yaml
  outline.candidates.yaml
  outline.selection.yaml
  length.options.yaml
  length.selection.yaml
  story.blueprint.yaml
  continuity.bible.yaml
  story.progression.plan.yaml
  paragraph.plan.yaml
  paragraphs/p001/
    paragraph.request.yaml
    neutral.paragraph.yaml
    sentence_anchor.matching.yaml
    sentence.plan.yaml
    source_sentence_anchor.selection.yaml
    paragraph.rewrite.plan.yaml
    candidate.output.yaml
    sentence_anchor.final_audit.yaml
    sentence_anchor.repair.plan.yaml
    repaired.candidate.output.yaml
    final.anchor.lock.yaml
    audit.report.yaml
    repair.plan.yaml
    final.paragraph.yaml
    paragraph.release.yaml
  story.assembly.yaml
  story.audit.report.yaml
  final.output.yaml
  final.text.repair.report.yaml
  final.text.repair.plan.yaml
  final.repaired.output.yaml
  final.repair.audit.yaml
  final.release.yaml
  run.decision.log.yaml
```

Schemas:

```text
references/schemas/phase4/writing-request.schema.yaml
references/schemas/phase4/outline-candidates.schema.yaml
references/schemas/phase4/story-blueprint.schema.yaml
references/schemas/phase4/paragraph-plan.schema.yaml
references/schemas/phase4/sentence-anchor-matching.schema.yaml
references/schemas/phase4/source-sentence-anchor-selection.schema.yaml
references/schemas/phase4/candidate-output.schema.yaml
references/schemas/phase4/sentence-anchor-final-audit.schema.yaml
references/schemas/phase4/final-output.schema.yaml
references/schemas/phase4/final-release.schema.yaml
references/schemas/phase45/final-text-repair.schema.yaml
```

Every final sentence must have a real source sentence anchor. Legacy
`sentence_pattern` artifacts are release blockers.
