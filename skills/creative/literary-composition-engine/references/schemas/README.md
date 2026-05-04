# Artifact Schema Contracts

These files define the required structure of generated YAML/JSON artifacts.
They are contract schemas, not scoring rubrics.

Rules:

- Do not add arbitrary style scores, confidence scores, strength values, or
  similarity numbers.
- Do not replace required explanations with labels such as `good`, `high`,
  `literary`, `philosophical`, or `elegant`.
- If an artifact needs extra information, put it under `notes`, `warnings`, or
  an explicitly named `*_findings` list.
- Runtime artifacts belong in the user's active workspace, never inside the
  skill directory.
- Generated artifacts may include additional provenance fields only when they
  do not change the meaning of required fields.

Schema files are organized by phase:

```text
phase1/   corpus preparation artifacts
phase2/   author pack construction artifacts
phase3/   validation and release gate artifacts
phase4/   writing runtime artifacts
phase45/  final text repair artifacts
```

