# Literary Composition Engine for Hermes

A Hermes-native experiment in high-style AI writing.

Literary composition is the benchmark: synopsis, paragraph, sentence, and phrase fused under deliberate pressure.

The bet is that if an agent can produce prose with serious literary value at this level of difficulty, lower-stakes forms of writing become downstream. Brand voice, ghostwriting, editorial memory, business prose, and artistic collaboration all become easier once the hardest version of style works.

This repository contains the Hermes skill used for the hackathon prototype, plus a demo story generated with the workflow.

Hermes defines the composition before the model starts writing.

## What It Does

The skill turns a literary corpus into an executable composition system:

1. **Phase 1: Corpus Preparation**  
   LLM subagents discover, extract, clean, and validate stories from messy source files. Python only persists the approved artifacts into SQLite.

2. **Phase 2: Author Pack Construction**  
   Agents build `theme.contract.yaml`, `style.contract.yaml`, `evidence.notes.yaml`, and `instruction.pairs.yaml`.

3. **Phase 3: Artifact Validation & Calibration**  
   Validators check that the contracts are evidenced, bounded, anti-pastiche, non-contradictory, and executable before writing is allowed.

4. **Phase 4: Writing Runtime**  
   Hermes interprets the user request, proposes outlines, asks for selection, creates a blueprint, plans paragraph by paragraph, drafts neutral content, and rewrites sentence by sentence using source sentence anchors.

5. **Phase 4.5: Final Text Repair**  
   A final repair gate audits weak sentence matches, local incoherence, false repairs, and obvious LLM slop before release.

Core invariant:

```text
agents decide; Python persists
```

## The Important Trick

The current canonical method is **sentence anchoring**, not generic sentence-pattern imitation.

For each target sentence, the runtime chooses a real sentence from the corpus whose syntactic/rhetorical movement is necessary for the planned target meaning. The source sentence acts as a formal machine: clause order, subordination, contrast, punctuation, cadence, and rhetorical motion. The new sentence carries different semantic content, but it must remain traceably modeled on that source sentence.

The skill explicitly rejects the older `sentence_patterns` approach. Pattern descriptions were too easy for the model to fake. Real source sentences are harder to evade and easier to audit.

The experiment asks whether style can be treated as a set of decomposable, teachable operations rather than an ineffable gift.

## Repository Layout

```text
skills/creative/literary-composition-engine/
  SKILL.md
  prompts/
  scripts/

examples/lovecraft/
  a-cor-do-lodo.pt-BR.md
  the-colour-of-sludge.en.md
```

Generated corpora, author packs, and run artifacts are not included. They are local working data and may contain source material from whatever corpus the operator provides.

## Running With Hermes

Install or copy the skill into your Hermes skills directory, then point Hermes at an author source directory.

Typical flow:

```text
Use the literary-composition-engine skill.
Prepare a corpus for <author_slug> from sources/<author_slug>/.
Run Phase 1 ingestion from zero.
Run Phase 2 author pack construction.
Run Phase 3 validation.
If Phase 3 allows generation, run Phase 4 and ask me to choose among 10 outlines.
After I choose an outline, suggest length options from corpus statistics and ask me to choose.
Then write the story using sentence-by-sentence source anchors and Phase 4.5 final repair.
```

The skill expects this project-local shape:

```text
sources/<author>/
corpus/<author>.db
author-models/<author>/
runs/<author>/<run_id>/
```

## Demo

The Lovecraft demo story is included in Portuguese and English:

- [A Cor do Lodo](examples/lovecraft/a-cor-do-lodo.pt-BR.md)
- [The Colour of Sludge](examples/lovecraft/the-colour-of-sludge.en.md)

The English file is a translation of the Portuguese demo output, included for presentation/readability.

## Why Literature

Literature is not the target market. It is the hard benchmark.

If AI can carry durable authorial voices at the highest point of style, it can become serious infrastructure for writing anywhere style matters. The goal is to test whether an agent can move beyond plausible meaning and generic fluency into controlled composition.

## What Is Not Included

No copyrighted corpus is included in this repository.

Operators are responsible for providing source files they are allowed to process. The skill can be tested on public-domain corpora or private corpora you have the right to use.

## Known Limitations

This is a hackathon prototype, not a finished product.

- Mechanical validation is necessary but not sufficient. Bad writing can still pass if validators check shallow artifacts instead of the source sentence itself.
- Cross-language source anchoring is harder than same-language anchoring.
- Some runs still need human steering when the model selects a poor source sentence for a planned target sentence.
- Final repair must preserve correct source-sentence mimicry. It should not "clean up" authorial weirdness into generic LLM prose.
- The validator must not accept invented license text such as "not-but structure allowed" unless that movement is visible in the actual source sentence.

## Why Hermes

This workflow uses Hermes-specific strengths:

- persistent memory and skill state for editable author packs
- isolated subagents for corpus extraction and validation
- model swapping for analysis, paraphrase, and audit stages
- long-running creative workflows with visible intermediate artifacts

Excellent one-shot prompts can produce excellent passages. The problem is that
quality is not reliably guaranteed. This skill turns literary composition into a
controlled runtime: plan, anchor, audit, repair, and release.
