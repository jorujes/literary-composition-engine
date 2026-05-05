# Literary Composition Engine for Hermes

Literary Composition Engine is a Hermes skill for building an author model from
a prose corpus and using it to write long-form text through plans, source
sentences, audits and repair gates.

The skill is built for the Hermes Agent Creative Hackathon. It uses literature
as the test case because literary prose makes weak composition easy to see:
paragraphs must carry pressure, sentences must have a reason to take their
shape, and word-list mimicry shows up quickly.

The repository contains the Hermes skill, the artifact schemas it expects, the
mechanical scripts used by the runtime, and a Lovecraft demo story generated
with the workflow.

## Documentation quick links

* [What the skill does](#what-the-skill-does)
* [Quick start](#quick-start)
* [Workspace layout](#workspace-layout)
* [The author pack](#the-author-pack)
* [Writing with source sentences](#writing-with-source-sentences)
* [Generated artifacts](#generated-artifacts)
* [Validation](#validation)
* [Demo](#demo)
* [Known limitations](#known-limitations)

## What the skill does

The skill runs four phases, plus a final repair pass:

1. **Corpus preparation.** Hermes turns source files into a SQLite corpus with
   stories, paragraphs and sentences.
2. **Author pack construction.** Hermes derives theme and style contracts from
   the corpus, with evidence and executable instruction pairs.
3. **Validation and calibration.** Hermes checks whether the author pack is
   complete, evidenced, bounded, non-contradictory and usable for generation.
4. **Writing runtime.** Hermes turns a user request into outlines, a blueprint,
   paragraph plans, neutral drafts and final prose written through real source
   sentence anchors.
5. **Final repair.** Hermes audits the assembled story for weak anchors, local
   incoherence, continuity drift and generic LLM prose before release.

The workflow is deliberately file-heavy. Each important decision is written to
an artifact that can be inspected later: what was planned, what was allowed,
what was blocked, which source sentence was used, what failed, what was
repaired and why the text was released.

The main rule is:

```text
agents decide; Python persists
```

Agents make literary and editorial decisions. Python creates databases, counts
tokens and paragraphs, indexes text, validates structure and assembles released
artifacts. Python does not choose anchors, interpret style, write final prose or
justify a weak literary decision.

## Quick start

Install or copy the skill into a Hermes skills directory, then provide a source
directory for an author.

A typical request to Hermes looks like this:

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

Generation starts only after Phase 3 has released a validated author pack.

## Workspace layout

The skill expects the active Hermes workspace to use this layout:

```text
sources/<author>/                         # user-provided source files
corpus/<author>.db                        # Phase 1 SQLite corpus
author-models/<author>/                   # Phase 2/3 author pack
runs/<author>/<run_id>/                   # Phase 4 writing runs
```

The skill itself is stored here:

```text
skills/creative/literary-composition-engine/
  SKILL.md
  references/
    prompts/
    schemas/
    artifact-schemas.md
  scripts/
    corpus_db.py
    validate_phase4_run.py
```

Generated corpora, author packs and run artifacts are not included in this
repository. They depend on the corpus supplied by the operator and may contain
source material.

## The author pack

Phase 2 builds an author pack along two axes.

The **theme** axis describes what kind of fictional world the corpus supports:

* `theme.world_rules`: how reality behaves in the author model.
* `theme.knowledge_path`: how ignorance, evidence, suspicion and recognition
  move through the work.
* `theme.human_stakes`: what kinds of loss, agency, fear, pressure or value
  matter.
* `theme.symbolic_operations`: which symbols perform semantic work, and under
  what conditions they must not be used.

The **style** axis describes how language moves:

* `style.narration_contract`: narrator distance, authority and knowledge
  limits.
* `style.thought_progression`: how a paragraph moves from observation to claim,
  qualification, reversal or consequence.
* `style.sentence_making`: how sentences are built.
* `style.diction_and_microchoices`: what lexical and connective choices do.

The resulting pack is written as:

```text
author-models/<author>/
  theme.contract.yaml
  style.contract.yaml
  evidence.notes.yaml
  instruction.pairs.yaml
```

Cards are procedural. A usable card says when to apply a move, when to block it,
what source evidence supports it, what failure looks like, and which repair is
allowed.

## Phase 3 gate

Before any story is written, Phase 3 checks the pack. Generation is blocked
unless:

```yaml
generation_allowed_for_phase_4: true
```

The validation pass looks for:

* missing cards or missing operational fields
* unsupported generation rules
* evidence without explicit limits
* decorative symbols
* wordlists presented as style
* sentence rules that only describe length
* vague tone commands
* contradictions between cards
* hypotheses accidentally used as generation rules

Approved artifacts are copied to:

```text
author-models/<author>/validated/
  theme.contract.yaml
  style.contract.yaml
  evidence.notes.yaml
  instruction.pairs.yaml
  phase3.release.yaml
```

## Writing with source sentences

The current writing method is literal source sentence anchoring.

For each planned target sentence, Hermes first writes the intended meaning of
that sentence. It then searches the corpus for real source sentences that can
carry that meaning formally. The chosen source sentence supplies a local
machine: clause order, subordination, contrast, cadence, punctuation behavior
and rhetorical motion.

The target sentence uses new semantic content. It must not copy the source
sentence's characters, images, events, conclusions or memorable phrases. It must
still be traceably modeled on the source sentence.

The direction is:

```text
planned target meaning
-> candidate source sentences
-> selected source sentence
-> target sentence
-> audit
-> repair or release
```

The reverse direction is blocked. Hermes should not pick an arbitrary source
sentence and then invent a reason why it fits.

The skill also blocks the older `sentence_patterns` approach. Pattern summaries
were too easy to fake. Literal source sentences give auditors something
concrete to compare.

## Paragraph runtime

Each paragraph is generated through its own artifact sequence:

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

The neutral paragraph states the content without authorial styling. The sentence
plan decides what each sentence must do. Source sentence selection happens only
after that plan exists.

A released paragraph must preserve meaning and continuity, obey the author
pack, use real source anchors, avoid decorative pastiche, and satisfy all Phase
3 runtime flags.

## Generated artifacts

The main generated files are documented in:

```text
skills/creative/literary-composition-engine/references/artifact-schemas.md
```

Schemas live under:

```text
skills/creative/literary-composition-engine/references/schemas/
  phase1/
  phase2/
  phase3/
  phase4/
  phase45/
```

They define required structure and allowed status values. They do not define
numeric style scores. Mechanical corpus statistics are allowed where useful;
arbitrary style strength, confidence or similarity scores are not part of the
runtime.

## Validation

The mechanical Phase 4 validator is:

```text
skills/creative/literary-composition-engine/scripts/validate_phase4_run.py
```

It checks that the run has the expected files, valid YAML, correct stage order,
paragraph releases, final release, source sentence anchors, decision logs and no
legacy pattern artifacts.

It catches structural failures. It does not replace literary judgment. A run can
still produce bad prose if Hermes chooses a merely convenient source sentence
instead of a necessary or sufficiently close one. The adversarial anchor audits
exist to catch that higher-level failure.

## Demo

The Lovecraft demo story is included in Portuguese and English:

* [A Cor do Lodo](examples/lovecraft/a-cor-do-lodo.pt-BR.md)
* [The Colour of Sludge](examples/lovecraft/the-colour-of-sludge.en.md)

The English file is a translation of the Portuguese demo output, included for
presentation and readability.

## Why Hermes

Hermes is useful here because the workflow is long-lived and artifact-heavy.
The skill uses:

* persistent files for author packs and run state
* subagents for corpus extraction, card construction, validation and audit
* model swapping for analysis, drafting, paraphrase and adversarial review
* visible intermediate artifacts that can be inspected, repaired and rerun

Strong one-shot prompts can produce strong paragraphs. This skill adds a record
of how a passage was planned, anchored, audited and repaired, so a good result
can be inspected instead of merely accepted.

## What is not included

No copyrighted corpus is included in this repository.

Operators are responsible for providing source files they are allowed to
process. The skill can be tested on public-domain corpora or private corpora
the operator has the right to use.

## Known limitations

This is a hackathon prototype.

* Mechanical validation is necessary but not sufficient.
* Anchor selection quality is still the hardest part of the runtime.
* Cross-language anchoring is harder than same-language anchoring.
* Long-form runs still benefit from human inspection when the corpus is small
  or stylistically varied.
* Final repair must preserve good source-sentence mimicry. It should not smooth
  authorial difficulty into generic LLM prose.
