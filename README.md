# Literary Composition Engine for Hermes

A Hermes-native experiment in controlled literary composition.

This project treats literature as the hardest benchmark for AI writing. The goal is not to make an LLM sound vaguely literary, or to ask for an author name and hope style appears. The goal is to turn style into an executable composition process: a sequence of corpus preparation, author-pack construction, validation, sentence-level anchoring, adversarial audit, repair, and release.

The premise is simple: slop appears when a statistical model is asked to continue language without a procedure for authorship. Fluency survives. Preference-shaped polish survives. But the ordered relation between premise, paragraph, sentence, and phrase usually collapses into generic motion.

Hermes gives that process a runtime. It prepares a corpus, builds editable author contracts, validates those contracts before writing, and then composes through plans and source-sentence anchors rather than free prompting.

If an agent can produce prose with serious literary value under this pressure, easier writing domains follow from the same machinery: brand voice, ghostwriting, editorial memory, business prose, creative collaboration, and any workflow where style must remain durable across sessions.

## Core Idea

The engine does not treat style as tone, word choice, or a bag of signature tokens. It treats style as composition under constraint.

A run is built around this chain:

```text
corpus
-> author pack
-> validation gate
-> user request
-> outline / selection
-> length choice
-> story blueprint
-> paragraph plan
-> neutral paragraph
-> sentence meaning plan
-> literal source-sentence anchor
-> target sentence
-> audit
-> repair
-> release
```

The important property is that writing does not begin as final prose. It begins as meaning, structure, and allowed operations. Final prose is only produced after the runtime knows what the paragraph must do and which real source sentences can carry the planned sentence meanings.

Core invariant:

```text
agents decide; Python persists
```

Agents make literary and editorial decisions. Python scripts create databases, count, index, validate, assemble, and persist artifacts. They do not choose stories, interpret style, select anchors, write final prose, or justify weak literary decisions.

## The Four Phases

### Phase 1: Corpus Preparation

Hermes starts from messy source files: EPUB, PDF, TXT, DOCX, or extracted text. LLM subagents discover works, extract story boundaries, clean text, and validate the result. Python stores accepted artifacts in SQLite.

The corpus database contains:

- `stories`
- `paragraphs`
- `sentences`
- full-text search tables
- ingestion logs

The sentence table is not incidental. It later supplies the literal source sentences used by the writing runtime.

### Phase 2: Author Pack Construction

Hermes builds an author pack from the corpus along two axes: theme and style.

The theme axis asks what kind of fictional world the author builds:

- `theme.world_rules`: what rules reality follows
- `theme.knowledge_path`: how ignorance becomes knowledge
- `theme.human_stakes`: what forms of value, agency, fear, loss, or pressure matter
- `theme.symbolic_operations`: which symbols actually perform semantic work, and when they must be blocked

The style axis asks how language behaves:

- `style.narration_contract`: who speaks, from what distance, with what authority and knowledge limits
- `style.thought_progression`: how thought moves across a paragraph
- `style.sentence_making`: how sentences are architected
- `style.diction_and_microchoices`: how lexical and connective choices function

The output is not a vibe profile. It is an operational author pack:

```text
author-models/<author>/
  theme.contract.yaml
  style.contract.yaml
  evidence.notes.yaml
  instruction.pairs.yaml
```

Each card must say what it controls, what it does not control, when to use it, when not to use it, which moves are allowed, which moves are prohibited, how failure looks, and how repair is allowed.

### Phase 3: Artifact Validation & Calibration

Before writing is allowed, Hermes validates the author pack.

This gate rejects:

- unsupported generative claims
- vague tone commands
- symbols used as decoration
- wordlists mistaken for style
- syntax described as sentence length rather than architecture
- evidence without limits
- conflicts between cards
- hypotheses promoted into generation rules
- cards that agents cannot execute without intuition

The result is a validated pack:

```text
author-models/<author>/validated/
  theme.contract.yaml
  style.contract.yaml
  evidence.notes.yaml
  instruction.pairs.yaml
  phase3.release.yaml
```

Phase 4 is blocked unless `phase3.release.yaml` explicitly says:

```yaml
generation_allowed_for_phase_4: true
```

### Phase 4: Writing Runtime

Phase 4 turns a user request into controlled prose.

Hermes may generate outline candidates, accept a user outline, rewrite a draft, continue a text, or write an isolated passage. For story generation, the user chooses an outline and a length option before the runtime locks the blueprint.

The runtime then creates:

```text
runs/<author>/<run_id>/
  writing.request.yaml
  outline.candidates.yaml
  outline.selection.yaml
  length.options.yaml
  length.selection.yaml
  story.blueprint.yaml
  continuity.bible.yaml
  story.progression.plan.yaml
  paragraph.plan.yaml
```

For each paragraph, Hermes creates a neutral paragraph first. The neutral paragraph carries the required meaning but no authorial style. Only after that does sentence-level anchoring begin.

## Sentence-Level Source Anchoring

The canonical writing method is literal source-sentence anchoring.

For every target sentence, the runtime must first define the target sentence's planned meaning. It then searches the corpus for real source sentences whose syntactic and rhetorical movement can carry that meaning. The selected source sentence acts as a formal machine.

A source sentence can contribute:

- clause order
- subordination
- contrast
- punctuation behavior
- cadence
- rhetorical motion
- placement of evidence, qualification, reversal, or conclusion
- relation between narrator, claim, observation, and consequence

The target sentence must carry different semantic content. It must not copy the source sentence's entities, memorable images, conclusions, or world facts. But it must remain traceably modeled on the source sentence.

This is why the engine rejects the older `sentence_patterns` approach. A pattern summary is too easy for a model to fake after the fact. A literal source sentence is harder to evade and easier to audit. The runtime can ask: does the target sentence actually inherit this sentence's movement, or is the explanation just retroactive handwaving?

Anchor selection is not allowed before the sentence meaning plan exists. A run is unreleasable if the parent process preselects anchors, passes recommended anchors into a delegate, or chooses a source sentence and then invents a target meaning around it. The direction must be:

```text
planned meaning -> candidate source sentences -> selected anchor -> target sentence
```

not:

```text
random source sentence -> target sentence -> justification
```

## Paragraph Runtime

Each paragraph has its own mini-runtime:

```text
paragraph.request.yaml
neutral.paragraph.yaml
sentence.plan.yaml
sentence_anchor.matching.yaml
source_sentence_anchor.selection.yaml
paragraph.rewrite.plan.yaml
candidate.output.yaml
blind_anchor_adversarial_audit.yaml
sentence_anchor.final_audit.yaml
final.anchor.lock.yaml
audit.report.yaml
repair.plan.yaml
final.paragraph.yaml
paragraph.release.yaml
```

A paragraph is released only after the runtime has checked:

- semantic preservation
- continuity with previously released paragraphs
- source-sentence fidelity
- theme/style instruction-pair application
- anti-pastiche constraints
- slop markers
- Phase 3 runtime flags
- absence of forbidden pattern artifacts

A failed sentence must be repaired by rewriting the target sentence or selecting a better source sentence. Improving the explanation is not repair.

## Final Repair

Phase 4.5 is a story-level repair gate. It exists because local paragraph approval is not enough.

The final repair pass checks:

- weak sentence anchors that survived local audit
- incoherent sentence-to-sentence transitions
- wrong repairs that flattened authorial weirdness into generic prose
- GPT-style filler and fake rhetorical structures
- continuity drift
- accumulated pastiche

Repair is conservative. It may fix local failures, but it may not invent new story content, activate new cards, or replace source-sentence anchoring with generic cleanup.

## Schemas And Validation

The skill includes artifact schemas under:

```text
skills/creative/literary-composition-engine/references/schemas/
```

Schemas define the expected structure of generated artifacts. They also encode release constraints and `must_not` rules. They are not scoring rubrics. The project deliberately avoids arbitrary numeric style scores, similarity scores, confidence values, or tone-strength sliders.

The schema tree covers:

```text
phase1/    corpus discovery, extraction, validation
phase2/    cards, contracts, evidence notes, instruction pairs
phase3/    validation manifests, claims, evidence traces, conflicts, release gates
phase4/    requests, outlines, blueprints, paragraph plans, anchors, audits, release
phase45/   final text repair
```

The mechanical validator lives at:

```text
skills/creative/literary-composition-engine/scripts/validate_phase4_run.py
```

It checks file presence, YAML parseability, stage ordering, paragraph release, final release, forbidden pattern artifacts, source-anchor requirements, and run-decision flags. It is necessary but not sufficient: a validator can catch structural cheating, but literary quality still depends on adversarial audits and real source-sentence fidelity.

## Repository Layout

```text
skills/creative/literary-composition-engine/
  SKILL.md
  references/
    prompts/
      discover_stories.md
      extract_story.md
      cleanup_story.md
      validate_story.md
      run_phase2_author_pack.md
      run_phase3_validation.md
      run_phase4_writing_runtime.md
      audit_phase4_sentence_anchor.md
      run_phase4_sentence_anchor_repair_pass.md
      run_phase45_final_text_repair.md
    schemas/
      phase1/
      phase2/
      phase3/
      phase4/
      phase45/
    artifact-schemas.md
  scripts/
    corpus_db.py
    validate_phase4_run.py

examples/lovecraft/
  a-cor-do-lodo.pt-BR.md
  the-colour-of-sludge.en.md
```

Generated corpora, author packs, and run artifacts are not included. They are local working data and may contain source material from whatever corpus the operator provides.

## Running With Hermes

Install or copy the skill into your Hermes skills directory, then provide an author source directory.

Typical request:

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

Expected workspace shape:

```text
sources/<author>/
corpus/<author>.db
author-models/<author>/
runs/<author>/<run_id>/
```

Once ingestion is finished, generation is still not a one-shot prompt. Hermes should ask for outline selection and length selection, then compose through blueprinting, paragraph planning, neutral drafting, source-sentence anchoring, audit, repair, and release.

## Demo

The Lovecraft demo story is included in Portuguese and English:

- [A Cor do Lodo](examples/lovecraft/a-cor-do-lodo.pt-BR.md)
- [The Colour of Sludge](examples/lovecraft/the-colour-of-sludge.en.md)

The English file is a translation of the Portuguese demo output, included for presentation/readability.

## Why Literature

Literature is the stress case because every weak assumption becomes visible. A model cannot hide behind ordinary usefulness when sentence architecture, paragraph pressure, image discipline, and rhetorical motion are all being judged at once.

The experiment asks whether style can be decomposed into teachable operations and enforced by an agentic system. If that works at the literary edge, then controlled style becomes infrastructure for less exacting forms of writing.

## Why Hermes

This workflow uses Hermes-specific strengths:

- persistent memory and skill state for editable author packs
- isolated subagents for corpus extraction, card construction, validation, audit, and repair
- model swapping for analysis, drafting, paraphrase, and adversarial review
- long-running workflows with visible intermediate artifacts
- local files that can be inspected, edited, rerun, and validated

The result can produce strong passages with good prompting, but the point is stronger than prompting. The skill makes quality inspectable. Every important decision leaves an artifact: what was planned, what evidence supported it, which source sentence was used, what was blocked, what failed, what was repaired, and why the text was released.

## What Is Not Included

No copyrighted corpus is included in this repository.

Operators are responsible for providing source files they are allowed to process. The skill can be tested on public-domain corpora or private corpora you have the right to use.

## Known Limitations

This is a hackathon prototype, not a finished product.

- Mechanical validation is necessary but not sufficient.
- A run can still fail if Hermes chooses merely convenient source sentences instead of necessary or sufficiently close formal machines.
- Cross-language source anchoring is harder than same-language anchoring.
- Long-form output still benefits from human inspection when the corpus is small or stylistically varied.
- Final repair must preserve correct source-sentence mimicry. It should not clean up authorial difficulty into generic LLM prose.
- The hardest unsolved problem is anchor selection quality: the system must keep improving its ability to find a source sentence whose movement genuinely fits the planned target meaning.
