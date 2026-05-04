# Phase 2 Author Pack Construction

Build persistent author contracts from an approved Phase 1 corpus.

Inputs:

```text
author_id
corpus/<author_id>.db
authorial-contract-rulebook.md or architecture.md
```

Outputs:

```text
author-models/<author_id>/
  theme.contract.yaml
  style.contract.yaml
  evidence.notes.yaml
  absorption.report.yaml
```

Required workflow:

1. Verify corpus exists and has accepted stories, paragraphs, and sentences.
2. Create `author-models/<author_id>/`.
3. Dispatch one card agent per required card whenever concurrency permits:
   - `theme.world_rules`
   - `theme.knowledge_path`
   - `theme.human_stakes`
   - `theme.symbolic_operations`
   - `style.narration_contract`
   - `style.thought_progression`
   - `style.sentence_making`
   - `style.diction_and_microchoices`
4. Each card agent must cite evidence from `corpus/<author_id>.db`; no outside works.
5. Merge card outputs into `theme.contract.yaml` and `style.contract.yaml`.
6. Build `evidence.notes.yaml` with traceable evidence objects.
7. Write `absorption.report.yaml` with `ready_for_phase3: true` only if all cards and evidence are structurally ready.

Non-negotiable rules:

- Do not use scores.
- Do not use labels like "philosophical", "elegant", "dark", or "melancholic" as commands.
- Do not treat symbols or lexical items as wordlists.
- Every important rule needs use conditions, non-use conditions, prohibited moves, examples, failure signs, and repair moves.
- Every `evidence_ref` must include `source_work`, `source_location`, `observed_behavior`, `supports_specific_claim`, `relevant_function`, and `not_a_license_for`.

Return final status, output paths, and blockers if any.
