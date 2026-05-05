#!/usr/bin/env python3
"""Mechanical validator for Phase 4 writing-runtime artifacts.

This script does not judge literary quality. It checks release conditions that
should not require taste: required files, YAML parsing, paragraph release
status, sentence mappings, final text presence, length/density gates, and
obvious source-anchor failures such as legacy sentence-pattern artifacts,
boilerplate alignment, or sequential source-sentence assignment.
"""

from __future__ import annotations

import argparse
import difflib
import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - environment dependent
    yaml = None


REQUIRED_PARAGRAPH_FILES = [
    "paragraph.request.yaml",
    "neutral.paragraph.yaml",
    "sentence.plan.yaml",
    "anchor.cycle.summary.yaml",
    "sentence_anchor.matching.yaml",
    "source_sentence_anchor.selection.yaml",
    "paragraph.rewrite.plan.yaml",
    "candidate.output.yaml",
    "blind_anchor_adversarial_audit.yaml",
    "audit.report.yaml",
    "sentence_anchor.final_audit.yaml",
    "final.anchor.lock.yaml",
    "final.paragraph.yaml",
    "paragraph.release.yaml",
]

PARAGRAPH_ARTIFACT_ORDER = [
    "sentence.plan.yaml",
    "sentence_anchor.matching.yaml",
    "source_sentence_anchor.selection.yaml",
    "paragraph.rewrite.plan.yaml",
    "candidate.output.yaml",
    "blind_anchor_adversarial_audit.yaml",
    "anchor.cycle.summary.yaml",
    "sentence_anchor.final_audit.yaml",
    "final.anchor.lock.yaml",
    "audit.report.yaml",
    "final.paragraph.yaml",
    "paragraph.release.yaml",
]

REQUIRED_PARAGRAPH_AUDIT_SECTIONS = [
    "semantic_preservation",
    "continuity_check",
    "theme_application",
    "style_application",
    "symbolic_policy_check",
    "anti_pastiche_check",
    "slop_check",
    "phase4_flags_check",
    "sentence_plan_check",
]

REQUIRED_SENTENCE_PLAN_FIELDS = [
    "sentence_id",
    "semantic_payload",
    "must_say",
    "must_not_say",
    "required_narrative_action",
]

OPTIONAL_PARAGRAPH_FILES = [
    "sentence_anchor.repair.plan.yaml",
    "repaired.candidate.output.yaml",
]

REQUIRED_STORY_FILES = [
    "story.assembly.yaml",
    "story.audit.report.yaml",
    "final.output.yaml",
    "final.text.repair.report.yaml",
    "final.repair.audit.yaml",
    "final.release.yaml",
    "run.decision.log.yaml",
]

OPTIONAL_STORY_FILES = [
    "final.text.repair.plan.yaml",
    "final.repaired.output.yaml",
]

GENERIC_ALIGNMENT_MARKERS = [
    "reuses only the formal operation",
    "declarative orientation, causal/concessive qualification, or controlled inventory",
    "Original target sentence about",
    "does not reuse source entities, setting, images, conclusion, or memorable phrasing",
    "Target content is original to this run",
    "source sentence text was not copied or exposed",
    "formal rhetorical move and clause skeleton",
    "punctuation and qualification frame",
    "comparada literalmente no motivo",
    "avaliada literalmente no motivo",
    "preserves source order of opening pressure",
    "delayed assertion and qualified closure",
    "chosen source provides a particular progression",
    "literal pressure to narrowed consequence",
    "other candidates either disperse the turn or close too abruptly",
    "starting from failed status, this passes because the target sentence performs the same local machine",
    "concrete pressure, controlled expansion, and narrowed implication",
    "initial pressure that delays full assertion",
    "turning phrase that redirects the sentence motion",
    "terminal cadence that narrows the implication",
    "same local machine",
    "source circumstance",
    "target substitutes survey circumstance",
]

LEGACY_PATTERN_KEYS = {
    "sentence_pattern_selection",
    "source_sentence_pattern_id",
    "selected_source_sentence_pattern_id",
    "pattern_structural_match",
    "why_this_pattern_is_necessary",
    "clause_skeleton",
    "structural_signature_used",
    "selected_pattern_id",
    "pattern_id",
}

SURFACE_GPTISM_PATTERNS = [
    (re.compile(r"\bnot\s+with\s+[^,.;:!?]+,\s+but\s+with\b", re.IGNORECASE), "not_with_but_with"),
    (re.compile(r"\bnot\s+[^,.;:!?]{1,80},\s+but\s+[^.;:!?]{1,120}", re.IGNORECASE), "not_x_but_y"),
]

NEUTRAL_STUB_LABEL_RE = re.compile(
    r"\bneutral\s+p\d{3}\s+sentence\s+\d+\s*:\s*",
    re.IGNORECASE,
)

STRICT_NOT_BUT_LICENSE_TERMS = [
    "not...but",
    "not-but",
    "not x but y",
    "not with",
    "not as",
    "rather than",
    "negation followed by corrective",
    "negative opening followed by corrective",
    "contrastive replacement",
    "corrective replacement",
]

PASSING_FORM_MATCH_STATUSES = {"strong_form_match", "acceptable_form_match"}
PASSING_ACTION_MATCH_VALUES = {"exact", "close"}

FORMAL_MATCH_CHECK_KEYS = [
    "mood_match",
    "clause_sequence_match",
    "coordination_subordination_match",
    "turn_logic_match",
    "punctuation_function_match",
    "category_fit",
]

ACTION_MATCH_KEYS = [
    "narrative_action_match",
    "entity_action_role_match",
]

TARGET_ACTION_FORM_KEYS = [
    "required_narrative_action_type",
    "required_entity_action_roles",
    "required_discourse_function",
]

SOURCE_ACTION_FORM_KEYS = [
    "source_narrative_action_type",
    "source_entity_action_roles",
    "source_discourse_function",
]

GENERIC_ACTION_MATCH_MARKERS = {
    "same broad action",
    "same broad movement",
    "same broad operation",
    "broadly similar",
    "broadly analogous",
    "roughly analogous",
    "analogous movement",
    "analogous rhetorical movement",
    "shares broad",
    "similar enough",
    "works by analogy",
    "analogy between source and target",
    "same general function",
    "same general movement",
    "fonte e alvo são análogos",
    "movimento parecido",
    "movimento semelhante",
    "ação parecida",
}

GENERIC_SOURCE_SPAN_MARKERS = {
    "opening syntax",
    "abertura sintática",
    "main clause",
    "oração principal",
    "clause skeleton",
    "source clause skeleton",
    "qualification",
    "qualificação",
    "development",
    "desenvolvimento",
    "opening",
    "abertura",
    "generic opening",
    "formal operation",
    "source words or span",
}

GENERIC_SEMANTIC_EXCLUSION_MARKERS = {
    "source semantics",
    "source semantic content",
    "source content",
    "source entities",
    "source images",
    "memorable phrasing",
    "do not copy source content",
    "do not copy source semantics",
    "semântica da fonte",
    "conteúdo da fonte",
    "imagens da fonte",
}

DIALECT_MARKERS = [
    r"\ban'\b",
    r"\bain't\b",
    r"\bnaow\b",
    r"\bfust\b",
    r"\brud\b",
    r"\bdaown\b",
    r"\bthey's\b",
    r"\bmis'\b",
    r"\bgen'ration\b",
    r"\bhaow\b",
    r"\bye\b",
]

STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "but",
    "by",
    "for",
    "from",
    "i",
    "in",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "were",
    "with",
    "o",
    "a",
    "os",
    "as",
    "de",
    "do",
    "da",
    "dos",
    "das",
    "e",
    "em",
    "que",
    "um",
    "uma",
    "para",
    "por",
    "com",
    "não",
}

WORD_RE = re.compile(r"[\wÀ-ÖØ-öø-ÿ']+")


def load_yaml(path: Path) -> Any:
    if yaml is None:
        raise SystemExit("PyYAML is required to validate Phase 4 artifacts. Install/use the Hermes runtime Python with yaml.")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def text_field(data: dict[str, Any], *names: str) -> str:
    for name in names:
        value = data.get(name)
        if isinstance(value, str):
            return value
    return ""


def artifact_root(data: Any, root_key: str) -> dict[str, Any]:
    if isinstance(data, dict):
        value = data.get(root_key)
        if isinstance(value, dict):
            return value
        return data
    return {}


def split_paragraphs(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"\n\s*\n", text.strip()) if part.strip()]


def normalize_prose(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip()).casefold()


def strip_neutral_stub_labels(text: str) -> str:
    return NEUTRAL_STUB_LABEL_RE.sub("", text or "")


def sentence_count(text: str) -> int:
    masked = re.sub(
        r"\b(?:[A-ZÀ-ÖØ-Þ]\.){2,}",
        lambda match: match.group(0).replace(".", "<DOT>"),
        text,
    )
    return len(re.findall(r"[^.!?…]+[.!?…]", masked))


def split_sentences(text: str) -> list[str]:
    masked = re.sub(
        r"\b(?:[A-ZÀ-ÖØ-Þ]\.){2,}",
        lambda match: match.group(0).replace(".", "<DOT>"),
        text or "",
    )
    parts = re.findall(r"[^.!?…]+[.!?…]", masked)
    return [part.replace("<DOT>", ".").strip() for part in parts if part.strip()]


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\wÀ-ÖØ-öø-ÿ]+\b", text or ""))


def normalized_words(text: str) -> list[str]:
    return [word.casefold() for word in WORD_RE.findall(text or "")]


def normalized_word_text(text: str) -> str:
    return " ".join(normalized_words(text))


def literal_spans(text: str, min_words: int, max_words: int = 9) -> set[str]:
    words = normalized_words(text)
    spans: set[str] = set()
    if len(words) < min_words:
        return spans
    max_n = min(max_words, len(words))
    for n in range(max_n, min_words - 1, -1):
        for start in range(0, len(words) - n + 1):
            span_words = words[start : start + n]
            content_words = [word for word in span_words if word not in STOPWORDS and len(word) > 2]
            if len(content_words) >= 2:
                spans.add(" ".join(span_words))
    return spans


def contains_literal_span(haystack: str, source_text: str, min_words: int) -> bool:
    haystack_words = normalized_word_text(haystack)
    if not haystack_words:
        return False
    return any(span in haystack_words for span in literal_spans(source_text, min_words=min_words))


def is_literal_source_span(span: Any, source_text: str, min_words: int) -> bool:
    span_text = normalized_word_text(flatten_text(span))
    source_words = normalized_word_text(source_text)
    if not span_text or not source_words or span_text not in source_words:
        return False
    if len(span_text.split()) < min_words:
        return False
    if any(char.isdigit() for char in flatten_text(span)):
        return True
    content_words = [word for word in span_text.split() if word not in STOPWORDS and len(word) > 2]
    return len(content_words) >= 1


def formal_check_passes(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.casefold() in {"yes", "true", "acceptable_difference"}
    return False


def has_generic_marker(value: Any) -> bool:
    haystack = flatten_text(value).casefold()
    return any(marker.casefold() in haystack for marker in GENERIC_ALIGNMENT_MARKERS)


def has_dialect_marker(text: str) -> bool:
    lowered = text or ""
    if "..." in lowered or ". . ." in lowered:
        return True
    return any(re.search(marker, lowered, re.IGNORECASE) for marker in DIALECT_MARKERS)


def flatten_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(flatten_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(flatten_text(item) for item in value)
    return ""


def duplicate_ratio(values: list[str]) -> float:
    cleaned = [value.strip() for value in values if isinstance(value, str) and value.strip()]
    if not cleaned:
        return 0.0
    counts: dict[str, int] = {}
    for value in cleaned:
        normalized = normalize_prose(value)
        counts[normalized] = counts.get(normalized, 0) + 1
    return max(counts.values()) / len(cleaned)


def similarity_ratio(left: str, right: str) -> float:
    left_norm = normalize_prose(left)
    right_norm = normalize_prose(right)
    if not left_norm or not right_norm:
        return 0.0
    return difflib.SequenceMatcher(None, left_norm, right_norm).ratio()


def repeated_items(values: list[str], max_count: int, min_words: int) -> list[tuple[str, int]]:
    counts: dict[str, tuple[str, int]] = {}
    for value in values:
        normalized = normalize_prose(value)
        if not normalized or word_count(value) < min_words:
            continue
        original, count = counts.get(normalized, (value.strip(), 0))
        counts[normalized] = (original, count + 1)
    repeated = [(original, count) for original, count in counts.values() if count > max_count]
    repeated.sort(key=lambda item: item[1], reverse=True)
    return repeated


def source_story_from_ref(ref: Any) -> str:
    if isinstance(ref, dict):
        value = ref.get("story_id")
        return value if isinstance(value, str) else ""
    return ""


def source_sentence_id_from_ref(ref: Any) -> int | None:
    if not isinstance(ref, dict):
        return None
    value = ref.get("sentence_id")
    return value if isinstance(value, int) else None


def source_ref_key(ref: Any) -> str:
    story = source_story_from_ref(ref)
    sentence_id = source_sentence_id_from_ref(ref)
    return f"{story}#{sentence_id}" if story and sentence_id is not None else ""


def missing_or_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict)):
        return not bool(value)
    return False


def is_generic_source_span(value: Any) -> bool:
    text = flatten_text(value).strip().casefold()
    if not text:
        return True
    normalized = re.sub(r"[^a-zà-öø-ÿ0-9 ]+", " ", text)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if normalized in GENERIC_SOURCE_SPAN_MARKERS:
        return True
    return any(marker in normalized for marker in GENERIC_SOURCE_SPAN_MARKERS if len(marker) > 10)


def is_generic_semantic_exclusion(value: Any) -> bool:
    text = flatten_text(value).strip().casefold()
    if not text:
        return True
    normalized = re.sub(r"[^a-zà-öø-ÿ0-9 ]+", " ", text)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if normalized in GENERIC_SEMANTIC_EXCLUSION_MARKERS:
        return True
    return any(marker in normalized for marker in GENERIC_SEMANTIC_EXCLUSION_MARKERS)


def is_generic_action_match_reason(value: Any) -> bool:
    text = flatten_text(value).strip().casefold()
    if word_count(text) < 14:
        return True
    if has_generic_marker(text):
        return True
    normalized = re.sub(r"[^a-zà-öø-ÿ0-9 ]+", " ", text)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return any(marker in normalized for marker in GENERIC_ACTION_MATCH_MARKERS)


def semantic_exclusion_items(entry: dict[str, Any]) -> list[Any]:
    keys = [
        "source_semantic_content_to_exclude",
        "semantic_cargo_to_exclude",
        "source_semantic_cargo_to_exclude",
        "semantic_content_not_to_copy",
        "source_content_not_to_copy",
        "must_not_copy_from_source_semantics",
    ]
    items: list[Any] = []
    for key in keys:
        value = entry.get(key)
        if isinstance(value, list):
            items.extend(value)
        elif isinstance(value, (dict, str)):
            items.append(value)
    return items


def source_part_semantic_exclusion_items(part: dict[str, Any]) -> list[Any]:
    keys = [
        "semantic_cargo_to_exclude",
        "source_semantic_cargo_to_exclude",
        "source_content_not_to_copy",
        "must_not_copy_from_source_semantics",
    ]
    items: list[Any] = []
    for key in keys:
        value = part.get(key)
        if isinstance(value, list):
            items.extend(value)
        elif isinstance(value, (dict, str)):
            items.append(value)
    return items


def forbidden_target_calques(entry: dict[str, Any]) -> list[str]:
    keys = [
        "target_language_forbidden_calques",
        "forbidden_target_calques",
        "target_forbidden_calques",
        "forbidden_target_phrases",
        "target_language_must_not_contain",
    ]
    phrases: list[str] = []
    for item in semantic_exclusion_items(entry):
        if isinstance(item, str):
            continue
        if not isinstance(item, dict):
            continue
        for key in keys:
            value = item.get(key)
            if isinstance(value, str):
                phrases.append(value)
            elif isinstance(value, list):
                phrases.extend(phrase for phrase in value if isinstance(phrase, str))
    return [phrase for phrase in phrases if word_count(phrase) >= 2]


def contains_phrase(text: str, phrase: str) -> bool:
    text_words = normalized_word_text(text)
    phrase_words = normalized_word_text(phrase)
    return bool(text_words and phrase_words and phrase_words in text_words)


def semicolon_count(text: str) -> int:
    return text.count(";") if isinstance(text, str) else 0


def longest_sequential_source_sentence_run(refs: list[Any]) -> int:
    longest = 0
    current = 0
    previous_story = ""
    previous_sentence_id: int | None = None
    for ref in refs:
        story = source_story_from_ref(ref)
        sentence_id = source_sentence_id_from_ref(ref)
        if story and sentence_id is not None and story == previous_story and previous_sentence_id is not None and sentence_id == previous_sentence_id + 1:
            current += 1
        else:
            current = 1
        longest = max(longest, current)
        previous_story = story
        previous_sentence_id = sentence_id
    return longest


def has_source_license_for_surface_pattern(mapping: dict[str, Any], selection_entry: dict[str, Any] | None) -> bool:
    source_license_parts: list[Any] = []
    if isinstance(selection_entry, dict):
        source_license_parts.extend(
            [
                selection_entry.get("selected_source_sentence_text"),
                selection_entry.get("source_sentence_parts"),
            ]
        )
    source_license_parts.append(mapping.get("source_sentence_fidelity"))
    haystack = " ".join(flatten_text(part) for part in source_license_parts).lower()
    return any(term in haystack for term in STRICT_NOT_BUT_LICENSE_TERMS)


def find_legacy_pattern_keys(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            next_path = f"{path}.{key}"
            if key in LEGACY_PATTERN_KEYS:
                hits.append(next_path)
            hits.extend(find_legacy_pattern_keys(item, next_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            hits.extend(find_legacy_pattern_keys(item, f"{path}[{index}]"))
    return hits


def validate(args: argparse.Namespace) -> int:
    run = args.run_dir
    findings: list[dict[str, Any]] = []

    def finding(kind: str, path: Path | str, message: str, blocking: bool = True) -> None:
        findings.append(
            {
                "kind": kind,
                "path": str(path),
                "message": message,
                "blocking": blocking,
            }
        )

    if not run.exists():
        finding("missing_run_dir", run, "run directory does not exist")
    else:
        for rel in REQUIRED_STORY_FILES:
            path = run / rel
            if not path.exists():
                finding("missing_story_file", path, f"missing {rel}")
            else:
                try:
                    load_yaml(path)
                except Exception as exc:  # noqa: BLE001
                    finding("yaml_parse_error", path, str(exc))

        decision_log_path = run / "run.decision.log.yaml"
        if decision_log_path.exists():
            try:
                decision_log = artifact_root(load_yaml(decision_log_path), "run_decision_log")
            except Exception:  # parse errors are already reported above
                decision_log = {}
            artifact_authorship = decision_log.get("artifact_authorship") if isinstance(decision_log, dict) else {}
            if not isinstance(artifact_authorship, dict):
                finding(
                    "run_decision_log_missing_artifact_authorship",
                    decision_log_path,
                    "run.decision.log.yaml must include artifact_authorship",
                )
                artifact_authorship = {}
            required_agent_authored = [
                "sentence_meaning_plan",
                "sentence_anchor_matching",
                "source_sentence_anchor_selection",
                "paragraph_rewrite_plan",
                "candidate_output",
                "anchor_audits",
                "final_paragraph",
                "final_output",
            ]
            for key in required_agent_authored:
                value = artifact_authorship.get(key)
                if value != "agent_direct":
                    finding(
                        "literary_artifact_not_agent_direct",
                        decision_log_path,
                        f"artifact_authorship.{key} must be agent_direct; got {value!r}",
                    )
            forbidden_methods = decision_log.get("forbidden_generation_methods_checked") if isinstance(decision_log, dict) else {}
            if not isinstance(forbidden_methods, dict):
                finding(
                    "run_decision_log_missing_forbidden_generation_methods",
                    decision_log_path,
                    "run.decision.log.yaml must include forbidden_generation_methods_checked",
                )
                forbidden_methods = {}
            forbidden_flags = [
                "python_or_shell_script_generated_final_text",
                "python_or_shell_script_generated_source_anchor_selection",
                "python_or_shell_script_generated_matching_reasons",
                "python_or_shell_script_generated_semantic_exclusions",
                "python_or_shell_script_generated_audit_judgments",
                "python_or_shell_script_processed_unreleased_final_or_candidate_text",
                "python_or_shell_script_counted_or_compared_unreleased_final_or_candidate_text",
                "parent_or_driver_preselected_source_anchors",
                "delegate_context_included_selected_source_anchors",
            ]
            for key in forbidden_flags:
                if forbidden_methods.get(key) is not False:
                    finding(
                        "forbidden_code_generated_literary_decision",
                        decision_log_path,
                        f"forbidden_generation_methods_checked.{key} must be false",
                    )
            for index, item in enumerate(decision_log.get("mechanical_tools_used") or []):
                if not isinstance(item, dict):
                    finding(
                        "bad_mechanical_tool_entry",
                        decision_log_path,
                        f"mechanical_tools_used[{index}] must be an object",
                    )
                    continue
                for key in [
                    "wrote_final_text",
                    "wrote_source_anchor_decisions",
                    "wrote_matching_reasons",
                    "wrote_semantic_exclusions",
                    "wrote_audit_judgments",
                    "processed_unreleased_final_or_candidate_text",
                ]:
                    if item.get(key) is not False:
                        finding(
                            "mechanical_tool_wrote_literary_decision",
                            decision_log_path,
                            f"mechanical_tools_used[{index}].{key} must be false",
                        )

    paragraph_count = args.paragraph_count
    released_count = 0
    sentence_mapping_count = 0
    final_texts: list[str] = []
    all_source_refs: list[Any] = []
    all_source_fidelity: list[str] = []
    all_semantic_independence: list[str] = []
    all_selection_reasons: list[str] = []
    all_blind_audit_reasons: list[str] = []
    all_blind_formal_differences: list[str] = []
    all_source_form_jobs: list[str] = []
    all_final_sentences: list[str] = []
    final_anchor_locks = 0
    final_anchor_repairs_required = 0

    for index in range(1, paragraph_count + 1):
        pid = f"p{index:03d}"
        pdir = run / "paragraphs" / pid
        if not pdir.exists():
            finding("missing_paragraph_dir", pdir, f"missing paragraph directory {pid}")
            continue

        loaded: dict[str, Any] = {}
        legacy_path = pdir / "sentence.pattern.selection.yaml"
        if legacy_path.exists():
            finding(
                "legacy_sentence_pattern_artifact_present",
                legacy_path,
                f"{pid} contains legacy sentence.pattern.selection.yaml; use source_sentence_anchor.selection.yaml",
            )
        for rel in REQUIRED_PARAGRAPH_FILES:
            path = pdir / rel
            if not path.exists():
                finding("missing_paragraph_file", path, f"missing {pid}/{rel}")
                continue
            try:
                loaded[rel] = load_yaml(path)
                legacy_hits = find_legacy_pattern_keys(loaded[rel])
                if legacy_hits:
                    finding(
                        "legacy_sentence_pattern_field_present",
                        path,
                        f"{pid}/{rel} contains forbidden legacy pattern field(s): {', '.join(legacy_hits[:8])}",
                    )
            except Exception as exc:  # noqa: BLE001
                finding("yaml_parse_error", path, str(exc))

        for rel in OPTIONAL_PARAGRAPH_FILES:
            path = pdir / rel
            if not path.exists():
                continue
            try:
                loaded[rel] = load_yaml(path)
                legacy_hits = find_legacy_pattern_keys(loaded[rel])
                if legacy_hits:
                    finding(
                        "legacy_sentence_pattern_field_present",
                        path,
                        f"{pid}/{rel} contains forbidden legacy pattern field(s): {', '.join(legacy_hits[:8])}",
                    )
            except Exception as exc:  # noqa: BLE001
                finding("yaml_parse_error", path, str(exc))

        existing_ordered_files = [rel for rel in PARAGRAPH_ARTIFACT_ORDER if (pdir / rel).exists()]
        for earlier, later in zip(existing_ordered_files, existing_ordered_files[1:]):
            earlier_path = pdir / earlier
            later_path = pdir / later
            try:
                if earlier_path.stat().st_mtime > later_path.stat().st_mtime:
                    finding(
                        "paragraph_artifact_order_violation",
                        later_path,
                        f"{pid}/{later} was written before {pid}/{earlier}; anchor selection/audit cannot be retrofitted after prose",
                    )
            except OSError:
                pass
        for producer, produced in [
            ("sentence_anchor.matching.yaml", "candidate.output.yaml"),
            ("source_sentence_anchor.selection.yaml", "candidate.output.yaml"),
            ("blind_anchor_adversarial_audit.yaml", "sentence_anchor.final_audit.yaml"),
            ("sentence_anchor.final_audit.yaml", "final.paragraph.yaml"),
            ("final.anchor.lock.yaml", "final.paragraph.yaml"),
            ("audit.report.yaml", "final.paragraph.yaml"),
        ]:
            producer_path = pdir / producer
            produced_path = pdir / produced
            if producer_path.exists() and produced_path.exists():
                try:
                    if producer_path.stat().st_mtime > produced_path.stat().st_mtime:
                        finding(
                            "paragraph_artifact_precondition_written_after_output",
                            produced_path,
                            f"{pid}/{produced} predates {pid}/{producer}; this indicates after-the-fact justification",
                        )
                except OSError:
                    pass

        release = artifact_root(loaded.get("paragraph.release.yaml"), "paragraph_release")
        if release.get("release_status") != "released":
            finding(
                "paragraph_not_released",
                pdir / "paragraph.release.yaml",
                f"{pid} release_status is not released",
            )
        else:
            released_count += 1

        final_paragraph = artifact_root(loaded.get("final.paragraph.yaml"), "final_paragraph")
        final_text = text_field(final_paragraph, "final_text", "text")
        if not final_text.strip():
            finding("missing_final_paragraph_text", pdir / "final.paragraph.yaml", f"{pid} has no final text")
        else:
            final_texts.append(final_text)
            all_final_sentences.extend(split_sentences(final_text))

        neutral = artifact_root(loaded.get("neutral.paragraph.yaml"), "neutral_paragraph")

        sentence_plan_root = artifact_root(loaded.get("sentence.plan.yaml"), "sentence_plan")
        sentence_plan_items = sentence_plan_root.get("sentences") if isinstance(sentence_plan_root, dict) else None
        if not isinstance(sentence_plan_items, list) or not sentence_plan_items:
            finding(
                "sentence_plan_missing_sentences",
                pdir / "sentence.plan.yaml",
                f"{pid} sentence.plan.yaml must include sentence_plan.sentences",
            )
        else:
            for item in sentence_plan_items:
                if not isinstance(item, dict):
                    finding("sentence_plan_bad_sentence_item", pdir / "sentence.plan.yaml", f"{pid} has non-object sentence plan item")
                    continue
                sid = item.get("sentence_id", "?")
                for field in REQUIRED_SENTENCE_PLAN_FIELDS:
                    if missing_or_empty(item.get(field)):
                        finding(
                            "sentence_plan_missing_operational_field",
                            pdir / "sentence.plan.yaml",
                            f"{pid}/{sid} sentence plan must include {field}",
                        )
                must_say = item.get("must_say")
                if not isinstance(must_say, list) or len([x for x in must_say if not missing_or_empty(x)]) < 2:
                    finding(
                        "sentence_plan_must_say_too_thin",
                        pdir / "sentence.plan.yaml",
                        f"{pid}/{sid} must_say must list at least two concrete semantic obligations",
                    )
                must_not_say = item.get("must_not_say")
                if not isinstance(must_not_say, list) or not [x for x in must_not_say if not missing_or_empty(x)]:
                    finding(
                        "sentence_plan_must_not_say_missing",
                        pdir / "sentence.plan.yaml",
                        f"{pid}/{sid} must_not_say must list concrete exclusions before anchoring",
                    )

        paragraph_audit_root = artifact_root(loaded.get("audit.report.yaml"), "audit_report")
        if paragraph_audit_root:
            if paragraph_audit_root.get("overall_status") == "passed":
                missing_sections = [key for key in REQUIRED_PARAGRAPH_AUDIT_SECTIONS if not isinstance(paragraph_audit_root.get(key), dict)]
                if missing_sections:
                    finding(
                        "paragraph_audit_too_shallow",
                        pdir / "audit.report.yaml",
                        f"{pid} audit.report.yaml is marked passed but lacks detailed sections: {', '.join(missing_sections)}",
                    )
                if paragraph_audit_root.get("findings") == [] and paragraph_audit_root.get("release_allowed") is True and missing_sections:
                    finding(
                        "paragraph_audit_empty_pass",
                        pdir / "audit.report.yaml",
                        f"{pid} audit.report.yaml is an empty pass; paragraph release requires concrete checks, not a placeholder",
                    )

        cycle_summary = loaded.get("anchor.cycle.summary.yaml") or {}
        if not isinstance(cycle_summary, dict) or "anchor_cycle_summary" not in cycle_summary:
            finding(
                "missing_anchor_cycle_summary_root",
                pdir / "anchor.cycle.summary.yaml",
                f"{pid} lacks anchor_cycle_summary",
            )
            cycle_summary_root = {}
        else:
            cycle_summary_root = cycle_summary.get("anchor_cycle_summary")
            if not isinstance(cycle_summary_root, dict):
                finding(
                    "bad_anchor_cycle_summary_root",
                    pdir / "anchor.cycle.summary.yaml",
                    f"{pid} anchor_cycle_summary must be an object",
                )
                cycle_summary_root = {}
        if cycle_summary_root:
            cycles_run = cycle_summary_root.get("cycles_run")
            if not isinstance(cycles_run, int) or cycles_run < 1:
                finding(
                    "anchor_cycle_summary_bad_cycle_count",
                    pdir / "anchor.cycle.summary.yaml",
                    f"{pid} cycles_run must be an integer >= 1",
                )
            if missing_or_empty(cycle_summary_root.get("approved_cycle")):
                finding(
                    "anchor_cycle_summary_missing_approved_cycle",
                    pdir / "anchor.cycle.summary.yaml",
                    f"{pid} lacks approved_cycle",
                )
            if cycle_summary_root.get("blind_adversarial_audit_required") is not True:
                finding(
                    "anchor_cycle_summary_blind_audit_not_required",
                    pdir / "anchor.cycle.summary.yaml",
                    f"{pid} must declare blind_adversarial_audit_required: true",
                )
            if cycle_summary_root.get("failed_sentence_repair_policy") != "rewrite_target_or_replace_source_never_rejustify":
                finding(
                    "anchor_cycle_summary_bad_repair_policy",
                    pdir / "anchor.cycle.summary.yaml",
                    f"{pid} failed_sentence_repair_policy must forbid justification-only repair",
                )
            cycle_results = cycle_summary_root.get("cycle_results")
            if not isinstance(cycle_results, list) or not cycle_results:
                finding(
                    "anchor_cycle_summary_missing_cycle_results",
                    pdir / "anchor.cycle.summary.yaml",
                    f"{pid} lacks cycle_results",
                )
            else:
                approved_cycle = cycle_summary_root.get("approved_cycle")
                approved_result = next(
                    (
                        item
                        for item in cycle_results
                        if isinstance(item, dict) and item.get("cycle_id") == approved_cycle
                    ),
                    None,
                )
                if not isinstance(approved_result, dict):
                    finding(
                        "anchor_cycle_summary_approved_cycle_not_in_results",
                        pdir / "anchor.cycle.summary.yaml",
                        f"{pid} approved_cycle is not represented in cycle_results",
                    )
                elif approved_result.get("copied_to_release_root") is not True:
                    finding(
                        "anchor_cycle_summary_not_copied_to_root",
                        pdir / "anchor.cycle.summary.yaml",
                        f"{pid} approved cycle must declare copied_to_release_root: true",
                    )
        blind_audit = loaded.get("blind_anchor_adversarial_audit.yaml") or {}
        if not isinstance(blind_audit, dict) or "blind_anchor_adversarial_audit" not in blind_audit:
            blind_root = {}
        else:
            blind_root = blind_audit.get("blind_anchor_adversarial_audit")
            if not isinstance(blind_root, dict):
                blind_root = {}
        blind_results: list[Any] = []
        if not blind_root:
            finding(
                "missing_blind_anchor_adversarial_audit_root",
                pdir / "blind_anchor_adversarial_audit.yaml",
                f"{pid} lacks blind_anchor_adversarial_audit",
            )
        else:
            if blind_root.get("auditor_visibility") != "source_target_payload_only":
                finding(
                    "blind_anchor_audit_not_blind",
                    pdir / "blind_anchor_adversarial_audit.yaml",
                    f"{pid} blind audit must declare auditor_visibility: source_target_payload_only",
                )
            if blind_root.get("initial_policy") != "all_sentences_failed_until_demonstrated":
                finding(
                    "blind_anchor_audit_bad_initial_policy",
                    pdir / "blind_anchor_adversarial_audit.yaml",
                    f"{pid} blind audit must start every sentence as failed_until_demonstrated",
                )
            if blind_root.get("overall_status") != "passed":
                finding(
                    "blind_anchor_audit_not_passed",
                    pdir / "blind_anchor_adversarial_audit.yaml",
                    f"{pid} blind audit overall_status is {blind_root.get('overall_status')!r}",
                )
            blind_results = blind_root.get("sentence_results") or blind_root.get("audit_items") or []
            if not isinstance(blind_results, list) or not blind_results:
                finding(
                    "blind_anchor_audit_missing_sentence_results",
                    pdir / "blind_anchor_adversarial_audit.yaml",
                    f"{pid} blind audit lacks sentence_results",
                )
            else:
                for result in blind_results:
                    if not isinstance(result, dict):
                        continue
                    sentence_id = result.get("sentence_id", "?")
                    if result.get("initial_status") != "failed_until_demonstrated":
                        finding(
                            "blind_anchor_audit_bad_initial_status",
                            pdir / "blind_anchor_adversarial_audit.yaml",
                            f"{pid}/{sentence_id} must begin as failed_until_demonstrated",
                        )
                    if result.get("verdict") != "passed":
                        finding(
                            "blind_anchor_audit_sentence_not_passed",
                            pdir / "blind_anchor_adversarial_audit.yaml",
                            f"{pid}/{sentence_id} verdict is {result.get('verdict')!r}",
                        )
                    if result.get("semantic_coherence_gate") not in {"passed", "clean"}:
                        finding(
                            "blind_anchor_audit_semantic_coherence_not_passed",
                            pdir / "blind_anchor_adversarial_audit.yaml",
                            f"{pid}/{sentence_id} semantic_coherence_gate is {result.get('semantic_coherence_gate')!r}",
                        )
                    source_literal = result.get("source_literal")
                    target_literal = result.get("target_literal")
                    if missing_or_empty(source_literal) or missing_or_empty(target_literal):
                        finding(
                            "blind_anchor_audit_missing_literals",
                            pdir / "blind_anchor_adversarial_audit.yaml",
                            f"{pid}/{sentence_id} must include source_literal and target_literal",
                        )
                    reason = result.get("concrete_reason")
                    if not isinstance(reason, str) or word_count(reason) < args.min_blind_audit_reason_words:
                        finding(
                            "blind_anchor_audit_reason_too_thin",
                            pdir / "blind_anchor_adversarial_audit.yaml",
                            f"{pid}/{sentence_id} concrete_reason is missing or too thin",
                        )
                    elif has_generic_marker(reason):
                        finding(
                            "blind_anchor_audit_generic_reason",
                            pdir / "blind_anchor_adversarial_audit.yaml",
                            f"{pid}/{sentence_id} concrete_reason uses generic anchor boilerplate",
                        )
                    else:
                        all_blind_audit_reasons.append(reason)
                        if isinstance(source_literal, str) and not contains_literal_span(reason, source_literal, args.min_literal_span_words):
                            finding(
                                "blind_anchor_audit_reason_missing_source_span",
                                pdir / "blind_anchor_adversarial_audit.yaml",
                                f"{pid}/{sentence_id} concrete_reason must quote or cite a literal source span",
                            )
                        if isinstance(target_literal, str) and not contains_literal_span(reason, target_literal, args.min_literal_span_words):
                            finding(
                                "blind_anchor_audit_reason_missing_target_span",
                                pdir / "blind_anchor_adversarial_audit.yaml",
                                f"{pid}/{sentence_id} concrete_reason must quote or cite a literal target span",
                            )
                    formal = result.get("formal_differences") or result.get("concrete_form_differences_examined")
                    if not isinstance(formal, dict):
                        finding(
                            "blind_anchor_audit_missing_formal_differences",
                            pdir / "blind_anchor_adversarial_audit.yaml",
                            f"{pid}/{sentence_id} lacks formal_differences",
                        )
                    else:
                        for key in [
                            "opening",
                            "clause_sequence",
                            "subordination_coordination",
                            "rhetorical_turn",
                            "closing",
                            "punctuation",
                            "length",
                            "movement_category",
                        ]:
                            value = formal.get(key)
                            if missing_or_empty(value) or flatten_text(value).strip().casefold() in {
                                "comparada literalmente no motivo",
                                "avaliada literalmente no motivo",
                                "categoria preservada conforme motivo",
                            } or has_generic_marker(value):
                                finding(
                                    "blind_anchor_audit_generic_formal_difference",
                                    pdir / "blind_anchor_adversarial_audit.yaml",
                                    f"{pid}/{sentence_id} formal_differences.{key} is missing or generic",
                                )
                        all_blind_formal_differences.append(flatten_text(formal))
        matching_artifact = loaded.get("sentence_anchor.matching.yaml") or {}
        matching_root = artifact_root(matching_artifact, "sentence_anchor_matching")
        matching_entries: dict[str, dict[str, Any]] = {}
        if not matching_root:
            finding(
                "missing_sentence_anchor_matching_root",
                pdir / "sentence_anchor.matching.yaml",
                f"{pid} lacks sentence_anchor_matching",
            )
        if matching_root.get("written_before_candidate_output") is not True:
            finding(
                "sentence_anchor_matching_not_prewrite",
                pdir / "sentence_anchor.matching.yaml",
                f"{pid} sentence_anchor.matching.yaml must declare written_before_candidate_output: true",
            )
        if matching_root.get("written_before_source_sentence_anchor_selection") is not True:
            finding(
                "sentence_anchor_matching_not_before_selection",
                pdir / "sentence_anchor.matching.yaml",
                f"{pid} sentence_anchor.matching.yaml must declare written_before_source_sentence_anchor_selection: true",
            )
        matching_sentences = matching_root.get("sentences") if isinstance(matching_root, dict) else None
        if not isinstance(matching_sentences, list) or not matching_sentences:
            finding(
                "sentence_anchor_matching_missing_sentences",
                pdir / "sentence_anchor.matching.yaml",
                f"{pid} sentence_anchor.matching.yaml has no sentences list",
            )
        else:
            for item in matching_sentences:
                if not isinstance(item, dict):
                    continue
                sentence_id = item.get("sentence_id")
                if isinstance(sentence_id, str):
                    matching_entries[sentence_id] = item
                target_form = item.get("target_form_requirements")
                if not isinstance(target_form, dict):
                    finding(
                        "sentence_anchor_matching_missing_target_form",
                        pdir / "sentence_anchor.matching.yaml",
                        f"{pid}/{sentence_id or '?'} lacks target_form_requirements",
                    )
                else:
                    required_form_keys = [
                        "required_mood",
                        "required_clause_sequence",
                        "required_turn_logic",
                        "required_punctuation_function",
                        "required_category_of_movement",
                        *TARGET_ACTION_FORM_KEYS,
                    ]
                    for key in required_form_keys:
                        if missing_or_empty(target_form.get(key)):
                            finding(
                                "sentence_anchor_matching_incomplete_target_form",
                                pdir / "sentence_anchor.matching.yaml",
                                f"{pid}/{sentence_id or '?'} target_form_requirements.{key} is missing or empty",
                            )
                selected_status = item.get("selected_form_match_status")
                if selected_status not in PASSING_FORM_MATCH_STATUSES:
                    finding(
                        "sentence_anchor_matching_selected_status_not_releasable",
                        pdir / "sentence_anchor.matching.yaml",
                        f"{pid}/{sentence_id or '?'} selected_form_match_status is {selected_status!r}",
                    )
                candidates = item.get("candidate_source_sentences")
                if not isinstance(candidates, list) or len(candidates) < args.min_source_candidates:
                    finding(
                        "sentence_anchor_matching_too_few_candidates",
                        pdir / "sentence_anchor.matching.yaml",
                        f"{pid}/{sentence_id or '?'} must record at least {args.min_source_candidates} form-matching candidates",
                    )
                else:
                    if not any(candidate.get("form_match_status") in PASSING_FORM_MATCH_STATUSES for candidate in candidates if isinstance(candidate, dict)):
                        finding(
                            "sentence_anchor_matching_no_passing_candidate",
                            pdir / "sentence_anchor.matching.yaml",
                            f"{pid}/{sentence_id or '?'} has no strong/acceptable candidate",
                        )
                    for candidate in candidates:
                        if not isinstance(candidate, dict):
                            continue
                        if missing_or_empty(candidate.get("source_sentence_text")):
                            finding(
                                "sentence_anchor_matching_candidate_missing_source_text",
                                pdir / "sentence_anchor.matching.yaml",
                                f"{pid}/{sentence_id or '?'} candidate lacks source_sentence_text",
                            )
                        if candidate.get("form_match_status") not in {
                            "strong_form_match",
                            "acceptable_form_match",
                            "weak_form_match",
                            "failed_form_match",
                        }:
                            finding(
                                "sentence_anchor_matching_bad_candidate_status",
                                pdir / "sentence_anchor.matching.yaml",
                                f"{pid}/{sentence_id or '?'} candidate form_match_status is {candidate.get('form_match_status')!r}",
                            )
                        form_analysis = candidate.get("source_form_analysis")
                        if not isinstance(form_analysis, dict) or missing_or_empty(form_analysis.get("mood")) or missing_or_empty(form_analysis.get("clause_sequence")):
                            finding(
                                "sentence_anchor_matching_incomplete_source_form",
                                pdir / "sentence_anchor.matching.yaml",
                                f"{pid}/{sentence_id or '?'} candidate lacks concrete source_form_analysis",
                            )
                        elif any(missing_or_empty(form_analysis.get(key)) for key in SOURCE_ACTION_FORM_KEYS):
                            finding(
                                "sentence_anchor_matching_incomplete_source_action_form",
                                pdir / "sentence_anchor.matching.yaml",
                                f"{pid}/{sentence_id or '?'} candidate source_form_analysis must declare source narrative action, entity/action roles, and discourse function",
                            )
                        form_status = candidate.get("form_match_status")
                        if form_status in PASSING_FORM_MATCH_STATUSES:
                            for key in ACTION_MATCH_KEYS:
                                if candidate.get(key) not in PASSING_ACTION_MATCH_VALUES:
                                    finding(
                                        "sentence_anchor_matching_candidate_action_match_not_releasable",
                                        pdir / "sentence_anchor.matching.yaml",
                                        f"{pid}/{sentence_id or '?'} passing candidate has {key}={candidate.get(key)!r}; expected exact or close",
                                    )
                            reason = candidate.get("why_action_match_is_not_loose_analogy")
                            if missing_or_empty(reason) or is_generic_action_match_reason(reason):
                                finding(
                                    "sentence_anchor_matching_candidate_action_reason_generic",
                                    pdir / "sentence_anchor.matching.yaml",
                                    f"{pid}/{sentence_id or '?'} passing candidate must explain concrete action fit, not loose analogy",
                                )
                if missing_or_empty(item.get("why_selected_before_writing")):
                    finding(
                        "sentence_anchor_matching_missing_prewrite_reason",
                        pdir / "sentence_anchor.matching.yaml",
                        f"{pid}/{sentence_id or '?'} lacks why_selected_before_writing",
                    )
                else:
                    prewrite_reason = flatten_text(item.get("why_selected_before_writing"))
                    selected_source_text = text_field(item, "selected_source_sentence_text")
                    if has_generic_marker(prewrite_reason):
                        finding(
                            "sentence_anchor_matching_generic_prewrite_reason",
                            pdir / "sentence_anchor.matching.yaml",
                            f"{pid}/{sentence_id or '?'} why_selected_before_writing uses generic anchor boilerplate",
                        )
                    if selected_source_text and not contains_literal_span(prewrite_reason, selected_source_text, args.min_literal_span_words):
                        finding(
                            "sentence_anchor_matching_prewrite_reason_missing_source_span",
                            pdir / "sentence_anchor.matching.yaml",
                            f"{pid}/{sentence_id or '?'} why_selected_before_writing must cite a literal span from the selected source sentence",
                        )
                for key in ACTION_MATCH_KEYS:
                    if item.get(key) not in PASSING_ACTION_MATCH_VALUES:
                        finding(
                            "sentence_anchor_matching_selected_action_match_not_releasable",
                            pdir / "sentence_anchor.matching.yaml",
                            f"{pid}/{sentence_id or '?'} selected {key} is {item.get(key)!r}; expected exact or close",
                        )
                action_reason = item.get("why_action_match_is_not_loose_analogy")
                if missing_or_empty(action_reason) or is_generic_action_match_reason(action_reason):
                    finding(
                        "sentence_anchor_matching_selected_action_reason_generic",
                        pdir / "sentence_anchor.matching.yaml",
                        f"{pid}/{sentence_id or '?'} selected source must justify concrete narrative/action fit, not loose analogy",
                    )
        final_audit = loaded.get("sentence_anchor.final_audit.yaml") or {}
        final_audit_root = final_audit.get("sentence_anchor_final_audit") if isinstance(final_audit, dict) else {}
        if not isinstance(final_audit_root, dict):
            final_audit_root = final_audit if isinstance(final_audit, dict) else {}
        if final_audit_root.get("overall_status") != "passed":
            finding(
                "sentence_anchor_final_audit_not_passed",
                pdir / "sentence_anchor.final_audit.yaml",
                f"{pid} final sentence-anchor audit overall_status is not passed",
            )
        repair_required = final_audit_root.get("repair_required") is True
        final_audit_results = final_audit_root.get("sentence_results")
        if not isinstance(final_audit_results, list) or not final_audit_results:
            finding(
                "sentence_anchor_final_audit_missing_results",
                pdir / "sentence_anchor.final_audit.yaml",
                f"{pid} final sentence-anchor audit has no sentence_results",
            )
        else:
            for result in final_audit_results:
                if not isinstance(result, dict):
                    continue
                sentence_id = result.get("sentence_id", "?")
                final_status = result.get("final_anchor_status")
                if final_status not in {"strong_anchor", "acceptable_anchor"}:
                    finding(
                        "sentence_anchor_final_status_not_releasable",
                        pdir / "sentence_anchor.final_audit.yaml",
                        f"{pid}/{sentence_id} final_anchor_status is {final_status!r}; expected strong_anchor or acceptable_anchor",
                    )
                if result.get("operation_match") not in {"exact", "close"}:
                    finding(
                        "sentence_anchor_operation_match_not_releasable",
                        pdir / "sentence_anchor.final_audit.yaml",
                        f"{pid}/{sentence_id} operation_match is {result.get('operation_match')!r}; expected exact or close",
                    )
                for key in ACTION_MATCH_KEYS:
                    if result.get(key) not in PASSING_ACTION_MATCH_VALUES:
                        finding(
                            "sentence_anchor_final_action_match_not_releasable",
                            pdir / "sentence_anchor.final_audit.yaml",
                            f"{pid}/{sentence_id} {key} is {result.get(key)!r}; expected exact or close",
                        )
                action_reason = result.get("why_action_match_is_not_loose_analogy")
                if missing_or_empty(action_reason) or is_generic_action_match_reason(action_reason):
                    finding(
                        "sentence_anchor_final_action_reason_generic",
                        pdir / "sentence_anchor.final_audit.yaml",
                        f"{pid}/{sentence_id} must justify concrete source/target action fit, not loose analogy",
                    )
                if not result.get("target_rhetorical_operation") or not result.get("source_rhetorical_operation"):
                    finding(
                        "sentence_anchor_missing_rhetorical_operation",
                        pdir / "sentence_anchor.final_audit.yaml",
                        f"{pid}/{sentence_id} must declare target and source rhetorical operations",
                    )
                prewrite_status = result.get("prewriting_form_match_status")
                if prewrite_status not in PASSING_FORM_MATCH_STATUSES:
                    finding(
                        "sentence_anchor_prewrite_form_match_not_releasable",
                        pdir / "sentence_anchor.final_audit.yaml",
                        f"{pid}/{sentence_id} prewriting_form_match_status is {prewrite_status!r}",
                    )
                checks = result.get("formal_match_checks")
                if not isinstance(checks, dict):
                    finding(
                        "sentence_anchor_missing_formal_match_checks",
                        pdir / "sentence_anchor.final_audit.yaml",
                        f"{pid}/{sentence_id} lacks formal_match_checks",
                    )
                else:
                    for key in FORMAL_MATCH_CHECK_KEYS:
                        value = checks.get(key)
                        if not formal_check_passes(value):
                            finding(
                                "sentence_anchor_formal_match_check_failed",
                                pdir / "sentence_anchor.final_audit.yaml",
                                f"{pid}/{sentence_id} formal_match_checks.{key} is {value!r}",
                            )
                if result.get("initial_anchor_status") in {"weak_anchor", "failed_anchor"}:
                    repair_required = True
                semantic_copy = result.get("semantic_copy_check")
                if not isinstance(semantic_copy, dict) or semantic_copy.get("finding") != "clean":
                    finding(
                        "sentence_anchor_semantic_copy_check_not_clean",
                        pdir / "sentence_anchor.final_audit.yaml",
                        f"{pid}/{sentence_id} semantic_copy_check must be present and clean",
                    )
        if repair_required:
            final_anchor_repairs_required += 1
            if "sentence_anchor.repair.plan.yaml" not in loaded:
                finding(
                    "missing_sentence_anchor_repair_plan",
                    pdir / "sentence_anchor.repair.plan.yaml",
                    f"{pid} final audit requires repair but sentence_anchor.repair.plan.yaml is missing",
                )
            if "repaired.candidate.output.yaml" not in loaded:
                finding(
                    "missing_repaired_candidate_output",
                    pdir / "repaired.candidate.output.yaml",
                    f"{pid} final audit requires repair but repaired.candidate.output.yaml is missing",
                )

        final_lock = loaded.get("final.anchor.lock.yaml") or {}
        final_lock_root = final_lock.get("final_anchor_lock") if isinstance(final_lock, dict) else {}
        if not isinstance(final_lock_root, dict):
            final_lock_root = final_lock if isinstance(final_lock, dict) else {}
        if final_lock_root.get("overall_status") != "locked":
            finding(
                "final_anchor_lock_not_locked",
                pdir / "final.anchor.lock.yaml",
                f"{pid} final anchor lock overall_status is not locked",
            )
        else:
            final_anchor_locks += 1
        locked_candidate_ref = text_field(final_lock_root, "locked_candidate_ref") or "candidate.output.yaml"
        if locked_candidate_ref not in {"candidate.output.yaml", "repaired.candidate.output.yaml"}:
            finding(
                "bad_locked_candidate_ref",
                pdir / "final.anchor.lock.yaml",
                f"{pid} locked_candidate_ref must be candidate.output.yaml or repaired.candidate.output.yaml",
            )
            locked_candidate_ref = "candidate.output.yaml"
        if locked_candidate_ref == "repaired.candidate.output.yaml" and "repaired.candidate.output.yaml" not in loaded:
            finding(
                "locked_repaired_candidate_missing",
                pdir / "final.anchor.lock.yaml",
                f"{pid} final lock points to repaired.candidate.output.yaml but the file is missing",
            )
        if locked_candidate_ref == "candidate.output.yaml" and final_lock_root.get("repairs_applied") is True:
            finding(
                "repairs_applied_but_candidate_not_repaired",
                pdir / "final.anchor.lock.yaml",
                f"{pid} repairs_applied is true but locked_candidate_ref is candidate.output.yaml",
            )
        sentence_locks = final_lock_root.get("sentence_locks")
        if not isinstance(sentence_locks, list) or not sentence_locks:
            finding("missing_sentence_locks", pdir / "final.anchor.lock.yaml", f"{pid} has no sentence_locks")
        else:
            for lock in sentence_locks:
                if not isinstance(lock, dict):
                    continue
                sentence_id = lock.get("sentence_id", "?")
                if lock.get("final_anchor_status") not in {"strong_anchor", "acceptable_anchor"}:
                    finding(
                        "locked_sentence_anchor_status_not_releasable",
                        pdir / "final.anchor.lock.yaml",
                        f"{pid}/{sentence_id} locked final_anchor_status is {lock.get('final_anchor_status')!r}",
                    )
                if lock.get("operation_match") not in {"exact", "close"}:
                    finding(
                        "locked_sentence_operation_match_not_releasable",
                        pdir / "final.anchor.lock.yaml",
                        f"{pid}/{sentence_id} locked operation_match is {lock.get('operation_match')!r}",
                    )
                for key in ACTION_MATCH_KEYS:
                    if lock.get(key) not in PASSING_ACTION_MATCH_VALUES:
                        finding(
                            "locked_sentence_action_match_not_releasable",
                            pdir / "final.anchor.lock.yaml",
                            f"{pid}/{sentence_id} locked {key} is {lock.get(key)!r}",
                        )
                action_reason = lock.get("why_action_match_is_not_loose_analogy")
                if missing_or_empty(action_reason) or is_generic_action_match_reason(action_reason):
                    finding(
                        "locked_sentence_action_reason_generic",
                        pdir / "final.anchor.lock.yaml",
                        f"{pid}/{sentence_id} lock must preserve concrete action-match justification",
                    )
                if not lock.get("target_rhetorical_operation") or not lock.get("source_rhetorical_operation"):
                    finding(
                        "locked_sentence_missing_rhetorical_operation",
                        pdir / "final.anchor.lock.yaml",
                        f"{pid}/{sentence_id} lock must declare target and source rhetorical operations",
                    )
                if lock.get("formal_match_status") not in PASSING_FORM_MATCH_STATUSES:
                    finding(
                        "locked_sentence_formal_match_status_not_releasable",
                        pdir / "final.anchor.lock.yaml",
                        f"{pid}/{sentence_id} formal_match_status is {lock.get('formal_match_status')!r}",
                    )

        candidate = artifact_root(loaded.get(locked_candidate_ref) or loaded.get("candidate.output.yaml"), "candidate_output")
        neutral_text = text_field(neutral, "neutral_text", "text")
        neutral_flat = flatten_text(neutral)
        if NEUTRAL_STUB_LABEL_RE.search(neutral_flat):
            finding(
                "neutral_draft_label_stub",
                pdir / "neutral.paragraph.yaml",
                f"{pid} neutral draft contains artificial sentence labels; neutral text must be plain content, not labeled final prose",
            )
        candidate_text = text_field(candidate, "candidate_text", "text")
        if not candidate_text.strip():
            finding(
                "missing_candidate_text",
                pdir / locked_candidate_ref,
                f"{pid} locked candidate has no candidate_text/text",
            )
        if candidate_text and final_text and candidate_text.strip() != final_text.strip():
            finding(
                "locked_candidate_differs_from_final_paragraph",
                pdir / locked_candidate_ref,
                f"{pid} locked candidate text does not match final.paragraph.yaml",
            )
        neutral_plain = normalize_prose(strip_neutral_stub_labels(neutral_text))
        candidate_plain = normalize_prose(candidate_text)
        final_plain = normalize_prose(final_text)
        neutral_candidate_similarity = similarity_ratio(strip_neutral_stub_labels(neutral_text), candidate_text)
        if neutral_candidate_similarity > args.max_neutral_candidate_similarity:
            finding(
                "candidate_too_similar_to_neutral",
                pdir / "candidate.output.yaml",
                f"{pid} candidate/neutral similarity is {neutral_candidate_similarity:.3f}, above {args.max_neutral_candidate_similarity:.3f}",
            )
        if candidate_plain and neutral_plain and candidate_plain == neutral_plain:
            finding("candidate_equals_neutral", pdir / "candidate.output.yaml", f"{pid} candidate equals neutral")
        if final_plain and neutral_plain and final_plain == neutral_plain:
            finding(
                "neutral_draft_is_labeled_final",
                pdir / "neutral.paragraph.yaml",
                f"{pid} neutral draft reduces to final prose after removing labels",
            )

        mappings = candidate.get("sentence_mapping")
        if not isinstance(mappings, list) or not mappings:
            finding("missing_sentence_mapping", pdir / "candidate.output.yaml", f"{pid} has no sentence_mapping")
        else:
            sentence_mapping_count += len(mappings)
            if isinstance(blind_results, list) and blind_results and len(blind_results) != len(mappings):
                finding(
                    "blind_anchor_audit_count_mismatch",
                    pdir / "blind_anchor_adversarial_audit.yaml",
                    f"{pid} blind audit has {len(blind_results)} sentence_results but candidate has {len(mappings)} mappings",
                )
            if isinstance(final_audit_results, list) and final_audit_results and len(final_audit_results) != len(mappings):
                finding(
                    "sentence_anchor_final_audit_count_mismatch",
                    pdir / "sentence_anchor.final_audit.yaml",
                    f"{pid} final audit has {len(final_audit_results)} sentence_results but candidate has {len(mappings)} mappings",
                )
            if isinstance(sentence_locks, list) and sentence_locks and len(sentence_locks) != len(mappings):
                finding(
                    "final_anchor_lock_count_mismatch",
                    pdir / "final.anchor.lock.yaml",
                    f"{pid} final anchor lock has {len(sentence_locks)} sentence_locks but candidate has {len(mappings)} mappings",
                )
            for mapping in mappings:
                if not isinstance(mapping, dict):
                    finding("bad_sentence_mapping", pdir / "candidate.output.yaml", f"{pid} mapping is not an object")
                    continue
                if not mapping.get("source_sentence_ref"):
                    finding(
                        "missing_source_sentence_ref",
                        pdir / "candidate.output.yaml",
                        f"{pid}/{mapping.get('sentence_id', '?')} lacks source_sentence_ref",
                    )
                if not mapping.get("source_sentence_text_hash"):
                    finding(
                        "missing_source_sentence_text_hash",
                        pdir / "candidate.output.yaml",
                        f"{pid}/{mapping.get('sentence_id', '?')} lacks source_sentence_text_hash",
                    )
                if not mapping.get("source_sentence_fidelity"):
                    finding(
                        "missing_source_sentence_fidelity",
                        pdir / "candidate.output.yaml",
                        f"{pid}/{mapping.get('sentence_id', '?')} lacks source_sentence_fidelity",
                    )
                if not mapping.get("target_semantic_independence"):
                    finding(
                        "missing_target_semantic_independence",
                        pdir / "candidate.output.yaml",
                        f"{pid}/{mapping.get('sentence_id', '?')} lacks target_semantic_independence",
                    )

        selection = loaded.get("source_sentence_anchor.selection.yaml") or {}
        if "source_sentence_anchor_selection" not in selection:
            finding(
                "missing_sentence_selection_root",
                pdir / "source_sentence_anchor.selection.yaml",
                f"{pid} lacks source_sentence_anchor_selection",
            )
        selection_entries: dict[str, dict[str, Any]] = {}
        selection_root = selection.get("source_sentence_anchor_selection") or {}
        planned = selection_root.get("planned_sentences") or selection_root.get("sentences") or []
        if isinstance(planned, list):
            for item in planned:
                if not isinstance(item, dict):
                    continue
                sentence_id = item.get("sentence_id")
                if isinstance(sentence_id, str):
                    selection_entries[sentence_id] = item
                reason = item.get("why_this_exact_sentence_is_necessary") or item.get("selected_because")
                if isinstance(reason, str) and reason.strip():
                    all_selection_reasons.append(reason)
                    selected_source_text = text_field(item, "selected_source_sentence_text")
                    if has_generic_marker(reason):
                        finding(
                            "source_anchor_selection_generic_reason",
                            pdir / "source_sentence_anchor.selection.yaml",
                            f"{pid}/{sentence_id or '?'} why_this_exact_sentence_is_necessary uses generic anchor boilerplate",
                        )
                    if selected_source_text and not contains_literal_span(reason, selected_source_text, args.min_literal_span_words):
                        finding(
                            "source_anchor_selection_reason_missing_source_span",
                            pdir / "source_sentence_anchor.selection.yaml",
                            f"{pid}/{sentence_id or '?'} why_this_exact_sentence_is_necessary must cite a literal span from the selected source sentence",
                        )
                else:
                    finding(
                        "source_anchor_selection_missing_reason",
                        pdir / "source_sentence_anchor.selection.yaml",
                        f"{pid}/{sentence_id or '?'} lacks why_this_exact_sentence_is_necessary",
                    )
                matching_entry = matching_entries.get(sentence_id) if isinstance(sentence_id, str) else None
                if not matching_entry:
                    finding(
                        "source_anchor_selection_missing_matching_entry",
                        pdir / "source_sentence_anchor.selection.yaml",
                        f"{pid}/{sentence_id or '?'} has no corresponding sentence_anchor.matching.yaml entry",
                    )
                if item.get("selected_form_match_status") not in PASSING_FORM_MATCH_STATUSES:
                    finding(
                        "source_anchor_selection_form_match_not_releasable",
                        pdir / "source_sentence_anchor.selection.yaml",
                        f"{pid}/{sentence_id or '?'} selected_form_match_status is {item.get('selected_form_match_status')!r}",
                    )
                if missing_or_empty(item.get("matching_ref")):
                    finding(
                        "source_anchor_selection_missing_matching_ref",
                        pdir / "source_sentence_anchor.selection.yaml",
                        f"{pid}/{sentence_id or '?'} lacks matching_ref",
                    )
                if missing_or_empty(item.get("target_form_requirements")):
                    finding(
                        "source_anchor_selection_missing_target_form",
                        pdir / "source_sentence_anchor.selection.yaml",
                        f"{pid}/{sentence_id or '?'} lacks target_form_requirements",
                    )
                else:
                    target_form = item.get("target_form_requirements")
                    if isinstance(target_form, dict):
                        for key in TARGET_ACTION_FORM_KEYS:
                            if missing_or_empty(target_form.get(key)):
                                finding(
                                    "source_anchor_selection_incomplete_target_action_form",
                                    pdir / "source_sentence_anchor.selection.yaml",
                                    f"{pid}/{sentence_id or '?'} target_form_requirements.{key} is missing or empty",
                                )
                if missing_or_empty(item.get("selected_source_form_analysis")):
                    finding(
                        "source_anchor_selection_missing_source_form_analysis",
                        pdir / "source_sentence_anchor.selection.yaml",
                        f"{pid}/{sentence_id or '?'} lacks selected_source_form_analysis",
                    )
                else:
                    source_form = item.get("selected_source_form_analysis")
                    if isinstance(source_form, dict):
                        for key in SOURCE_ACTION_FORM_KEYS:
                            if missing_or_empty(source_form.get(key)):
                                finding(
                                    "source_anchor_selection_incomplete_source_action_form",
                                    pdir / "source_sentence_anchor.selection.yaml",
                                    f"{pid}/{sentence_id or '?'} selected_source_form_analysis.{key} is missing or empty",
                                )
                for key in ACTION_MATCH_KEYS:
                    if item.get(key) not in PASSING_ACTION_MATCH_VALUES:
                        finding(
                            "source_anchor_selection_action_match_not_releasable",
                            pdir / "source_sentence_anchor.selection.yaml",
                            f"{pid}/{sentence_id or '?'} {key} is {item.get(key)!r}; expected exact or close",
                        )
                action_reason = item.get("why_action_match_is_not_loose_analogy")
                if missing_or_empty(action_reason) or is_generic_action_match_reason(action_reason):
                    finding(
                        "source_anchor_selection_action_reason_generic",
                        pdir / "source_sentence_anchor.selection.yaml",
                        f"{pid}/{sentence_id or '?'} must explain concrete source/target narrative action fit, not loose analogy",
                    )
                if not item.get("selected_source_sentence_text"):
                    finding(
                        "missing_selected_source_sentence_text",
                        pdir / "source_sentence_anchor.selection.yaml",
                        f"{pid}/{sentence_id or '?'} lacks selected_source_sentence_text",
                    )
                if not isinstance(item.get("candidate_source_sentences_considered"), list) or len(item.get("candidate_source_sentences_considered") or []) < args.min_source_candidates:
                    finding(
                        "missing_rejected_source_sentence_candidates",
                        pdir / "source_sentence_anchor.selection.yaml",
                        f"{pid}/{sentence_id or '?'} must record at least {args.min_source_candidates} candidate source sentences considered",
                    )
                else:
                    for candidate in item.get("candidate_source_sentences_considered") or []:
                        if isinstance(candidate, dict) and candidate.get("form_match_status") not in {
                            "strong_form_match",
                            "acceptable_form_match",
                            "weak_form_match",
                            "failed_form_match",
                        }:
                            finding(
                                "source_anchor_selection_candidate_missing_form_status",
                                pdir / "source_sentence_anchor.selection.yaml",
                                f"{pid}/{sentence_id or '?'} candidate lacks valid form_match_status",
                            )
                        if isinstance(candidate, dict) and candidate.get("form_match_status") in PASSING_FORM_MATCH_STATUSES:
                            for key in ACTION_MATCH_KEYS:
                                if candidate.get(key) not in PASSING_ACTION_MATCH_VALUES:
                                    finding(
                                        "source_anchor_selection_candidate_action_match_not_releasable",
                                        pdir / "source_sentence_anchor.selection.yaml",
                                        f"{pid}/{sentence_id or '?'} passing candidate has {key}={candidate.get(key)!r}; expected exact or close",
                                    )
                exclusions = semantic_exclusion_items(item)
                if not exclusions:
                    finding(
                        "source_anchor_selection_missing_semantic_exclusions",
                        pdir / "source_sentence_anchor.selection.yaml",
                        f"{pid}/{sentence_id or '?'} must list source semantic content/images/phrasing excluded from the target",
                    )
                else:
                    has_source_phrase = False
                    has_forbidden_calque = False
                    for exclusion in exclusions:
                        if is_generic_semantic_exclusion(exclusion):
                            finding(
                                "source_anchor_selection_generic_semantic_exclusion",
                                pdir / "source_sentence_anchor.selection.yaml",
                                f"{pid}/{sentence_id or '?'} has generic semantic exclusion: {flatten_text(exclusion)[:160]!r}",
                            )
                        if isinstance(exclusion, dict):
                            source_phrase = exclusion.get("source_phrase") or exclusion.get("source_content") or exclusion.get("source_image_or_entity")
                            if isinstance(source_phrase, str) and word_count(source_phrase) >= 2:
                                has_source_phrase = True
                            if forbidden_target_calques({"source_semantic_content_to_exclude": [exclusion]}):
                                has_forbidden_calque = True
                    if not has_source_phrase:
                        finding(
                            "source_anchor_selection_missing_excluded_source_phrase",
                            pdir / "source_sentence_anchor.selection.yaml",
                            f"{pid}/{sentence_id or '?'} semantic exclusions must name concrete source phrase/content to exclude",
                        )
                    if not has_forbidden_calque:
                        finding(
                            "source_anchor_selection_missing_forbidden_target_calques",
                            pdir / "source_sentence_anchor.selection.yaml",
                            f"{pid}/{sentence_id or '?'} semantic exclusions must include target-language forbidden calques",
                        )
                source_parts = item.get("source_sentence_parts")
                if not isinstance(source_parts, list) or not source_parts:
                    finding(
                        "source_anchor_selection_missing_source_parts",
                        pdir / "source_sentence_anchor.selection.yaml",
                        f"{pid}/{sentence_id or '?'} lacks source_sentence_parts",
                    )
                else:
                    selected_source_text = text_field(item, "selected_source_sentence_text")
                    for part in source_parts:
                        if not isinstance(part, dict):
                            continue
                        span = part.get("source_words_or_span")
                        if is_generic_source_span(span):
                            finding(
                                "source_anchor_selection_generic_source_span",
                                pdir / "source_sentence_anchor.selection.yaml",
                                f"{pid}/{sentence_id or '?'} has generic source_words_or_span: {span!r}",
                            )
                        elif selected_source_text and not is_literal_source_span(span, selected_source_text, args.min_source_part_span_words):
                            finding(
                                "source_anchor_selection_nonliteral_source_span",
                                pdir / "source_sentence_anchor.selection.yaml",
                                f"{pid}/{sentence_id or '?'} source_words_or_span is not literal in selected source sentence: {span!r}",
                            )
                        if missing_or_empty(part.get("formal_job")) or is_generic_source_span(part.get("formal_job")) or has_generic_marker(part.get("formal_job")):
                            finding(
                                "source_anchor_selection_generic_formal_job",
                                pdir / "source_sentence_anchor.selection.yaml",
                                f"{pid}/{sentence_id or '?'} has generic formal_job: {part.get('formal_job')!r}",
                            )
                        else:
                            all_source_form_jobs.append(flatten_text(part.get("formal_job")))
                        part_exclusions = source_part_semantic_exclusion_items(part)
                        if not part_exclusions:
                            finding(
                                "source_anchor_selection_missing_part_semantic_cargo_exclusion",
                                pdir / "source_sentence_anchor.selection.yaml",
                                f"{pid}/{sentence_id or '?'} source part {span!r} must declare semantic_cargo_to_exclude with target-language forbidden calques",
                            )
                        else:
                            has_part_source_phrase = False
                            has_part_forbidden_calque = False
                            for exclusion in part_exclusions:
                                if is_generic_semantic_exclusion(exclusion):
                                    finding(
                                        "source_anchor_selection_generic_part_semantic_cargo_exclusion",
                                        pdir / "source_sentence_anchor.selection.yaml",
                                        f"{pid}/{sentence_id or '?'} source part {span!r} has generic semantic cargo exclusion: {flatten_text(exclusion)[:160]!r}",
                                    )
                                if isinstance(exclusion, dict):
                                    source_phrase = exclusion.get("source_phrase") or exclusion.get("source_content") or exclusion.get("source_image_or_entity")
                                    if isinstance(source_phrase, str) and word_count(source_phrase) >= 2:
                                        has_part_source_phrase = True
                                        span_words = normalized_word_text(flatten_text(span))
                                        phrase_words = normalized_word_text(source_phrase)
                                        if span_words and phrase_words and phrase_words not in span_words:
                                            finding(
                                                "source_anchor_selection_excluded_phrase_outside_part",
                                                pdir / "source_sentence_anchor.selection.yaml",
                                                f"{pid}/{sentence_id or '?'} excluded source_phrase {source_phrase!r} is not inside source part {span!r}",
                                            )
                                    if forbidden_target_calques({"semantic_cargo_to_exclude": [exclusion]}):
                                        has_part_forbidden_calque = True
                            if not has_part_source_phrase:
                                finding(
                                    "source_anchor_selection_missing_part_excluded_source_phrase",
                                    pdir / "source_sentence_anchor.selection.yaml",
                                    f"{pid}/{sentence_id or '?'} source part {span!r} must name the source semantic cargo being excluded",
                                )
                            if not has_part_forbidden_calque:
                                finding(
                                    "source_anchor_selection_missing_part_forbidden_target_calques",
                                    pdir / "source_sentence_anchor.selection.yaml",
                                    f"{pid}/{sentence_id or '?'} source part {span!r} must list target-language calques forbidden in the target sentence",
                                )

        alignments = selection.get("source_to_target_alignment_plan") or selection_root.get("source_to_target_alignment_plan") or []
        if isinstance(alignments, list):
            for item in alignments:
                if not isinstance(item, dict):
                    continue
                fidelity = item.get("source_sentence_fidelity") or item.get("source_to_target_part_map")
                if isinstance(fidelity, str) and fidelity.strip():
                    all_source_fidelity.append(fidelity)
                elif isinstance(fidelity, list):
                    all_source_fidelity.append(flatten_text(fidelity))
                    for part_map in fidelity:
                        if not isinstance(part_map, dict):
                            continue
                        span = part_map.get("source_words_or_span")
                        if is_generic_source_span(span):
                            finding(
                                "source_alignment_generic_source_span",
                                pdir / "source_sentence_anchor.selection.yaml",
                                f"{pid}/{item.get('sentence_id', '?')} alignment has generic source_words_or_span: {span!r}",
                            )
                        elif text_field(item, "source_sentence_text") and not is_literal_source_span(span, text_field(item, "source_sentence_text"), args.min_source_part_span_words):
                            finding(
                                "source_alignment_nonliteral_source_span",
                                pdir / "source_sentence_anchor.selection.yaml",
                                f"{pid}/{item.get('sentence_id', '?')} alignment source_words_or_span is not literal in source_sentence_text: {span!r}",
                            )
                        if missing_or_empty(part_map.get("source_formal_job")) or is_generic_source_span(part_map.get("source_formal_job")) or has_generic_marker(part_map.get("source_formal_job")):
                            finding(
                                "source_alignment_generic_formal_job",
                                pdir / "source_sentence_anchor.selection.yaml",
                                f"{pid}/{item.get('sentence_id', '?')} alignment has generic source_formal_job: {part_map.get('source_formal_job')!r}",
                            )
                        else:
                            all_source_form_jobs.append(flatten_text(part_map.get("source_formal_job")))
                independence = item.get("target_semantic_independence")
                if isinstance(independence, str) and independence.strip():
                    all_semantic_independence.append(independence)

        final_sentence_count = sentence_count(final_text)
        if mappings and final_sentence_count and len(mappings) != final_sentence_count:
            finding(
                "sentence_mapping_count_mismatch",
                pdir / "candidate.output.yaml",
                f"{pid} has {len(mappings)} mappings but {final_sentence_count} final sentences",
            )
        if isinstance(mappings, list):
            for mapping in mappings:
                if not isinstance(mapping, dict):
                    continue
                source_ref = mapping.get("source_sentence_ref")
                if isinstance(source_ref, dict):
                    all_source_refs.append(source_ref)
                fidelity = mapping.get("source_sentence_fidelity")
                if isinstance(fidelity, str) and fidelity.strip():
                    all_source_fidelity.append(fidelity)
                independence = mapping.get("target_semantic_independence")
                if isinstance(independence, str) and independence.strip():
                    all_semantic_independence.append(independence)
                output_sentence = text_field(mapping, "output_sentence", "target_sentence", "text")
                selection_entry = selection_entries.get(str(mapping.get("sentence_id")))
                if output_sentence and isinstance(selection_entry, dict):
                    source_text = text_field(selection_entry, "selected_source_sentence_text")
                    selected_status = selection_entry.get("selected_form_match_status")
                    if source_text:
                        source_words = max(1, word_count(source_text))
                        target_words = max(1, word_count(output_sentence))
                        length_ratio = max(source_words / target_words, target_words / source_words)
                        if selected_status == "strong_form_match" and length_ratio > args.max_strong_anchor_length_ratio:
                            finding(
                                "strong_source_anchor_length_mismatch",
                                pdir / "candidate.output.yaml",
                                f"{pid}/{mapping.get('sentence_id', '?')} strong_form_match has source/target length ratio {length_ratio:.2f}, above {args.max_strong_anchor_length_ratio:.2f}",
                            )
                        if selected_status == "acceptable_form_match" and length_ratio > args.max_acceptable_anchor_length_ratio:
                            finding(
                                "acceptable_source_anchor_length_mismatch",
                                pdir / "candidate.output.yaml",
                                f"{pid}/{mapping.get('sentence_id', '?')} acceptable_form_match has source/target length ratio {length_ratio:.2f}, above {args.max_acceptable_anchor_length_ratio:.2f}",
                            )
                        if has_dialect_marker(source_text) and not has_dialect_marker(output_sentence):
                            finding(
                                "source_anchor_dialect_mismatch",
                                pdir / "candidate.output.yaml",
                                f"{pid}/{mapping.get('sentence_id', '?')} selected dialect/fragmentary source sentence for non-dialect target",
                            )
                        if "?" in source_text and "?" not in output_sentence and selected_status == "strong_form_match":
                            finding(
                                "strong_source_anchor_question_to_declaration",
                                pdir / "candidate.output.yaml",
                                f"{pid}/{mapping.get('sentence_id', '?')} strong_form_match uses a question source for a non-question target",
                            )
                        source_semicolons = semicolon_count(source_text)
                        target_semicolons = semicolon_count(output_sentence)
                        if target_semicolons > source_semicolons:
                            finding(
                                "source_anchor_unlicensed_semicolon",
                                pdir / "candidate.output.yaml",
                                f"{pid}/{mapping.get('sentence_id', '?')} target uses {target_semicolons} semicolon(s) but source uses {source_semicolons}; semicolons must come from the selected source sentence, not from generic model style",
                            )
                    for calque in forbidden_target_calques(selection_entry):
                        if contains_phrase(output_sentence, calque):
                            finding(
                                "source_semantic_calque_copied",
                                pdir / "candidate.output.yaml",
                                f"{pid}/{mapping.get('sentence_id', '?')} target contains forbidden source-content calque: {calque!r}",
                            )
                    for part in selection_entry.get("source_sentence_parts") or []:
                        if not isinstance(part, dict):
                            continue
                        for calque in forbidden_target_calques(part):
                            if contains_phrase(output_sentence, calque):
                                finding(
                                    "source_part_semantic_calque_copied",
                                    pdir / "candidate.output.yaml",
                                    f"{pid}/{mapping.get('sentence_id', '?')} target contains forbidden source-part calque: {calque!r}",
                                )
                for regex, label in SURFACE_GPTISM_PATTERNS:
                    if output_sentence and regex.search(output_sentence):
                        if not has_source_license_for_surface_pattern(mapping, selection_entry):
                            finding(
                                "unlicensed_generic_rhetorical_template",
                                pdir / "candidate.output.yaml",
                                f"{pid}/{mapping.get('sentence_id', '?')} uses {label} without explicit source-sentence license",
                            )

    final_output_path = run / "final.output.yaml"
    if final_output_path.exists():
        final_output = artifact_root(load_yaml(final_output_path), "final_output")
        if not isinstance(final_output.get("final_text"), str) or not final_output.get("final_text", "").strip():
            finding("missing_required_final_text_key", final_output_path, "final.output.yaml must include non-empty final_text")
        story_text = text_field(final_output, "final_text", "text")
        if not story_text.strip():
            finding("missing_final_output_text", final_output_path, "final.output.yaml has no final_text/text")
        if final_output.get("paragraph_count") != paragraph_count:
            finding(
                "paragraph_count_mismatch",
                final_output_path,
                f"paragraph_count is {final_output.get('paragraph_count')}, expected {paragraph_count}",
            )
        blocks = split_paragraphs(story_text)
        if len(blocks) != paragraph_count:
            finding(
                "final_text_paragraph_count_mismatch",
                final_output_path,
                f"final text has {len(blocks)} paragraph blocks, expected {paragraph_count}",
            )
        hits = [token for token in args.forbidden_token if token.lower() in story_text.lower()]
        if hits:
            finding("forbidden_tokens_found", final_output_path, f"forbidden tokens found: {', '.join(hits)}")
        total_words = word_count(story_text)
        paragraph_word_counts = [word_count(block) for block in blocks]
        if args.min_total_words and total_words < args.min_total_words:
            finding(
                "total_word_count_below_floor",
                final_output_path,
                f"final text has {total_words} words, below minimum {args.min_total_words}",
            )
        if args.max_total_words and total_words > args.max_total_words:
            finding(
                "total_word_count_above_ceiling",
                final_output_path,
                f"final text has {total_words} words, above maximum {args.max_total_words}",
            )
        if paragraph_word_counts:
            median_paragraph_words = sorted(paragraph_word_counts)[len(paragraph_word_counts) // 2]
            if args.min_median_paragraph_words and median_paragraph_words < args.min_median_paragraph_words:
                finding(
                    "median_paragraph_words_below_floor",
                    final_output_path,
                    f"median paragraph has {median_paragraph_words} words, below minimum {args.min_median_paragraph_words}",
                )
            short_paragraphs = sum(1 for count in paragraph_word_counts if count < args.min_paragraph_words)
            if args.min_paragraph_words and short_paragraphs:
                finding(
                    "paragraph_words_below_floor",
                    final_output_path,
                    f"{short_paragraphs} paragraph(s) below minimum {args.min_paragraph_words} words",
                )

    repair_report_path = run / "final.text.repair.report.yaml"
    repair_required_by_report = False
    if repair_report_path.exists():
        repair_report = load_yaml(repair_report_path)
        repair_report_root = repair_report.get("final_text_repair_report") if isinstance(repair_report, dict) else {}
        if not isinstance(repair_report_root, dict):
            repair_report_root = repair_report if isinstance(repair_report, dict) else {}
        overall_finding = repair_report_root.get("overall_finding")
        if overall_finding not in {"clean", "repair_required"}:
            finding(
                "final_text_repair_report_not_releasable",
                repair_report_path,
                f"final text repair overall_finding is {overall_finding!r}; expected clean or repair_required",
            )
        repair_required_by_report = overall_finding == "repair_required"
        findings_list = repair_report_root.get("findings")
        if findings_list is None or not isinstance(findings_list, list):
            finding("final_text_repair_report_missing_findings", repair_report_path, "final text repair report must include findings list")

    final_repair_audit_path = run / "final.repair.audit.yaml"
    audited_output_ref = "final.output.yaml"
    if final_repair_audit_path.exists():
        repair_audit = load_yaml(final_repair_audit_path)
        repair_audit_root = repair_audit.get("final_repair_audit") if isinstance(repair_audit, dict) else {}
        if not isinstance(repair_audit_root, dict):
            repair_audit_root = repair_audit if isinstance(repair_audit, dict) else {}
        if repair_audit_root.get("overall_status") != "passed":
            finding(
                "final_repair_audit_not_passed",
                final_repair_audit_path,
                f"final repair audit overall_status is {repair_audit_root.get('overall_status')!r}",
            )
        if repair_audit_root.get("release_allowed") is not True:
            finding("final_repair_audit_release_not_allowed", final_repair_audit_path, "final repair audit release_allowed is not true")
        if repair_audit_root.get("blockers"):
            finding("final_repair_audit_blockers_present", final_repair_audit_path, "final.repair.audit.yaml has blockers")
        audited_value = repair_audit_root.get("audited_output_ref")
        if isinstance(audited_value, str) and audited_value.strip():
            audited_output_ref = audited_value

    repair_plan_path = run / "final.text.repair.plan.yaml"
    repaired_output_path = run / "final.repaired.output.yaml"
    if repair_required_by_report:
        if not repair_plan_path.exists():
            finding("missing_final_text_repair_plan", repair_plan_path, "final text repair report requires repair but plan is missing")
        if not repaired_output_path.exists():
            finding("missing_final_repaired_output", repaired_output_path, "final text repair report requires repair but final.repaired.output.yaml is missing")
    for path in [repair_plan_path, repaired_output_path]:
        if path.exists():
            try:
                load_yaml(path)
            except Exception as exc:  # noqa: BLE001
                finding("yaml_parse_error", path, str(exc))

    final_release_path = run / "final.release.yaml"
    approved_output_ref = "final.output.yaml"
    if final_release_path.exists():
        final_release = artifact_root(load_yaml(final_release_path), "final_release")
        if final_release.get("release_status") != "released":
            finding("final_not_released", final_release_path, "final release_status is not released")
        if final_release.get("blockers"):
            finding("final_blockers_present", final_release_path, "final.release.yaml has blockers")
        release_approved = final_release.get("approved_output_ref")
        if not isinstance(release_approved, str) or release_approved not in {"final.output.yaml", "final.repaired.output.yaml"}:
            finding(
                "final_release_missing_approved_output_ref",
                final_release_path,
                "final.release.yaml must set approved_output_ref to final.output.yaml or final.repaired.output.yaml",
            )
        else:
            approved_output_ref = release_approved
        repair_status = final_release.get("final_text_repair_status")
        if repair_status not in {"clean", "repaired"}:
            finding(
                "final_release_missing_repair_status",
                final_release_path,
                "final.release.yaml must set final_text_repair_status to clean or repaired",
            )
        if final_release.get("final_repair_audit_ref") != "final.repair.audit.yaml":
            finding(
                "final_release_missing_repair_audit_ref",
                final_release_path,
                "final.release.yaml must set final_repair_audit_ref: final.repair.audit.yaml",
            )
        if repair_required_by_report and repair_status != "repaired":
            finding("final_release_repair_status_mismatch", final_release_path, "repair report required repair but final_text_repair_status is not repaired")
        if repair_status == "clean" and approved_output_ref != "final.output.yaml":
            finding("final_release_clean_points_to_repaired_output", final_release_path, "clean final text repair status must approve final.output.yaml")
        if repair_status == "repaired" and approved_output_ref != "final.repaired.output.yaml":
            finding("final_release_repaired_points_to_original_output", final_release_path, "repaired final text repair status must approve final.repaired.output.yaml")
        if approved_output_ref != audited_output_ref:
            finding(
                "final_release_audited_output_mismatch",
                final_release_path,
                f"approved_output_ref {approved_output_ref!r} does not match final repair audit audited_output_ref {audited_output_ref!r}",
            )

    approved_output_path = run / approved_output_ref
    if not approved_output_path.exists():
        finding("approved_output_missing", approved_output_path, f"approved output {approved_output_ref} does not exist")
    elif approved_output_ref == "final.repaired.output.yaml":
        approved_output = artifact_root(load_yaml(approved_output_path), "final_output")
        approved_text = text_field(approved_output, "final_text", "text")
        if not approved_text.strip():
            finding("missing_approved_output_text", approved_output_path, f"{approved_output_ref} has no final_text/text")
        blocks = split_paragraphs(approved_text)
        if len(blocks) != paragraph_count:
            finding(
                "approved_output_paragraph_count_mismatch",
                approved_output_path,
                f"approved output has {len(blocks)} paragraph blocks, expected {paragraph_count}",
            )
        total_words = word_count(approved_text)
        if args.min_total_words and total_words < args.min_total_words:
            finding(
                "approved_output_word_count_below_floor",
                approved_output_path,
                f"approved output has {total_words} words, below minimum {args.min_total_words}",
            )
        paragraph_word_counts = [word_count(block) for block in blocks]
        if paragraph_word_counts:
            median_paragraph_words = sorted(paragraph_word_counts)[len(paragraph_word_counts) // 2]
            if args.min_median_paragraph_words and median_paragraph_words < args.min_median_paragraph_words:
                finding(
                    "approved_output_median_paragraph_words_below_floor",
                    approved_output_path,
                    f"approved output median paragraph has {median_paragraph_words} words, below minimum {args.min_median_paragraph_words}",
                )

    if sentence_mapping_count:
        if args.max_repeated_final_sentence_count:
            repeated_final_sentences = repeated_items(
                all_final_sentences,
                args.max_repeated_final_sentence_count,
                args.min_repeated_final_sentence_words,
            )
            if repeated_final_sentences:
                example, count = repeated_final_sentences[0]
                finding(
                    "repeated_final_sentence",
                    run,
                    f"final sentence repeated {count} times (max {args.max_repeated_final_sentence_count}): {example[:220]}",
                )
        if all_source_refs:
            story_counts: dict[str, int] = {}
            for source_ref in all_source_refs:
                story = source_story_from_ref(source_ref)
                if story:
                    story_counts[story] = story_counts.get(story, 0) + 1
            if story_counts:
                top_story, top_count = max(story_counts.items(), key=lambda item: item[1])
                ratio = top_count / len(all_source_refs)
                if args.max_source_story_ratio and ratio > args.max_source_story_ratio:
                    finding(
                        "source_anchor_story_overconcentrated",
                        run,
                        f"{top_count}/{len(all_source_refs)} sentence anchors ({ratio:.2%}) come from {top_story}; max allowed is {args.max_source_story_ratio:.0%}",
                    )
            seq_run = longest_sequential_source_sentence_run(all_source_refs)
            if args.max_sequential_source_sentence_run and seq_run > args.max_sequential_source_sentence_run:
                finding(
                    "source_sentence_anchor_sequential_assignment",
                    run,
                    f"longest sequential source sentence run is {seq_run}; max allowed is {args.max_sequential_source_sentence_run}",
                )

        fidelity_ratio = duplicate_ratio(all_source_fidelity)
        if args.max_duplicate_source_fidelity_ratio and fidelity_ratio > args.max_duplicate_source_fidelity_ratio:
            finding(
                "boilerplate_source_sentence_fidelity",
                run,
                f"most repeated source_sentence_fidelity/source alignment text covers {fidelity_ratio:.2%} of mapped sentences; max allowed is {args.max_duplicate_source_fidelity_ratio:.0%}",
            )
        semantic_ratio = duplicate_ratio(all_semantic_independence)
        if args.max_duplicate_semantic_independence_ratio and semantic_ratio > args.max_duplicate_semantic_independence_ratio:
            finding(
                "boilerplate_target_semantic_independence",
                run,
                f"most repeated target_semantic_independence text covers {semantic_ratio:.2%} of mapped sentences; max allowed is {args.max_duplicate_semantic_independence_ratio:.0%}",
            )
        reason_ratio = duplicate_ratio(all_selection_reasons)
        if all_selection_reasons and args.max_duplicate_selection_reason_ratio and reason_ratio > args.max_duplicate_selection_reason_ratio:
            finding(
                "boilerplate_anchor_selection_reason",
                run,
                f"most repeated anchor-selection reason covers {reason_ratio:.2%} of planned sentences; max allowed is {args.max_duplicate_selection_reason_ratio:.0%}",
            )
        blind_reason_ratio = duplicate_ratio(all_blind_audit_reasons)
        if len(all_blind_audit_reasons) >= args.min_items_for_duplicate_boilerplate_check and args.max_duplicate_blind_reason_ratio and blind_reason_ratio > args.max_duplicate_blind_reason_ratio:
            finding(
                "boilerplate_blind_anchor_audit_reason",
                run,
                f"most repeated blind concrete_reason covers {blind_reason_ratio:.2%} of audited sentences; max allowed is {args.max_duplicate_blind_reason_ratio:.0%}",
            )
        blind_formal_ratio = duplicate_ratio(all_blind_formal_differences)
        if len(all_blind_formal_differences) >= args.min_items_for_duplicate_boilerplate_check and args.max_duplicate_blind_formal_ratio and blind_formal_ratio > args.max_duplicate_blind_formal_ratio:
            finding(
                "boilerplate_blind_anchor_formal_differences",
                run,
                f"most repeated blind formal_differences block covers {blind_formal_ratio:.2%} of audited sentences; max allowed is {args.max_duplicate_blind_formal_ratio:.0%}",
            )
        source_form_job_ratio = duplicate_ratio(all_source_form_jobs)
        if len(all_source_form_jobs) >= args.min_items_for_duplicate_boilerplate_check and args.max_duplicate_source_form_job_ratio and source_form_job_ratio > args.max_duplicate_source_form_job_ratio:
            finding(
                "boilerplate_source_form_jobs",
                run,
                f"most repeated source formal job covers {source_form_job_ratio:.2%} of mapped source parts; max allowed is {args.max_duplicate_source_form_job_ratio:.0%}",
            )
        generic_hits = [
            marker
            for marker in GENERIC_ALIGNMENT_MARKERS
            if marker.lower() in " ".join(all_source_fidelity + all_semantic_independence + all_selection_reasons + all_blind_audit_reasons + all_blind_formal_differences + all_source_form_jobs).lower()
        ]
        if generic_hits:
            finding(
                "generic_alignment_marker_found",
                run,
                f"generic alignment marker(s) found: {', '.join(generic_hits[:5])}",
            )

    blocking_findings = [item for item in findings if item["blocking"]]
    report = {
        "run_dir": str(run),
        "paragraph_count_expected": paragraph_count,
        "released_paragraphs": released_count,
        "sentence_mappings": sentence_mapping_count,
        "approved_output_ref": approved_output_ref,
        "source_anchor_summary": {
            "unique_source_sentences": len({source_ref_key(ref) for ref in all_source_refs if source_ref_key(ref)}),
            "longest_sequential_source_sentence_run": longest_sequential_source_sentence_run(all_source_refs),
            "source_fidelity_duplicate_ratio": duplicate_ratio(all_source_fidelity),
            "semantic_independence_duplicate_ratio": duplicate_ratio(all_semantic_independence),
            "selection_reason_duplicate_ratio": duplicate_ratio(all_selection_reasons),
            "blind_reason_duplicate_ratio": duplicate_ratio(all_blind_audit_reasons),
            "blind_formal_differences_duplicate_ratio": duplicate_ratio(all_blind_formal_differences),
            "source_form_job_duplicate_ratio": duplicate_ratio(all_source_form_jobs),
            "final_anchor_locks": final_anchor_locks,
            "paragraphs_requiring_final_anchor_repair": final_anchor_repairs_required,
        },
        "blocking_findings": blocking_findings,
        "warnings": [item for item in findings if not item["blocking"]],
        "passed": not blocking_findings,
    }

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        if yaml is None:
            raise SystemExit("PyYAML is required to write the validation report.")
        args.report.write_text(yaml.safe_dump(report, allow_unicode=True, sort_keys=False), encoding="utf-8")
    if yaml is None:
        raise SystemExit("PyYAML is required to print the validation report.")
    print(yaml.safe_dump(report, allow_unicode=True, sort_keys=False))
    return 0 if not blocking_findings else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate Phase 4 writing-runtime artifacts")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--paragraph-count", type=int, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--min-total-words", type=int, default=0)
    parser.add_argument("--max-total-words", type=int, default=0)
    parser.add_argument("--min-median-paragraph-words", type=int, default=0)
    parser.add_argument("--min-paragraph-words", type=int, default=0)
    parser.add_argument("--max-source-story-ratio", type=float, default=0.0, help="Optional run-specific source-story concentration ceiling; 0 disables.")
    parser.add_argument("--max-sequential-source-sentence-run", type=int, default=0, help="Optional run-specific sequential-anchor ceiling; 0 disables.")
    parser.add_argument("--max-duplicate-source-fidelity-ratio", type=float, default=0.0, help="Optional run-specific duplicate-fidelity ceiling; 0 disables.")
    parser.add_argument("--max-duplicate-semantic-independence-ratio", type=float, default=0.0, help="Optional run-specific duplicate-independence ceiling; 0 disables.")
    parser.add_argument("--max-duplicate-selection-reason-ratio", type=float, default=0.0, help="Optional run-specific duplicate-selection-reason ceiling; 0 disables.")
    parser.add_argument("--max-neutral-candidate-similarity", type=float, default=0.92, help="Block paragraph candidates that are effectively the neutral draft.")
    parser.add_argument("--max-repeated-final-sentence-count", type=int, default=1, help="Block exact repeated final sentences above this count; use 0 to disable.")
    parser.add_argument("--min-repeated-final-sentence-words", type=int, default=8, help="Minimum sentence length for repeated-final-sentence blocking.")
    parser.add_argument("--min-blind-audit-reason-words", type=int, default=18, help="Minimum length for concrete blind audit reasons.")
    parser.add_argument("--min-literal-span-words", type=int, default=4, help="Minimum contiguous source/target words that must be cited in strict anchor reasons.")
    parser.add_argument("--min-source-part-span-words", type=int, default=2, help="Minimum words for source_words_or_span to count as a literal source part.")
    parser.add_argument("--min-source-candidates", type=int, default=5, help="Minimum source candidates considered per planned sentence.")
    parser.add_argument("--max-strong-anchor-length-ratio", type=float, default=2.15, help="Maximum source/target word-count ratio for strong_form_match anchors.")
    parser.add_argument("--max-acceptable-anchor-length-ratio", type=float, default=3.0, help="Maximum source/target word-count ratio for acceptable_form_match anchors.")
    parser.add_argument("--max-duplicate-blind-reason-ratio", type=float, default=0.35, help="Maximum duplicate blind concrete_reason ratio; 0 disables.")
    parser.add_argument("--max-duplicate-blind-formal-ratio", type=float, default=0.35, help="Maximum duplicate blind formal_differences ratio; 0 disables.")
    parser.add_argument("--max-duplicate-source-form-job-ratio", type=float, default=0.35, help="Maximum duplicate source formal job ratio; 0 disables.")
    parser.add_argument("--min-items-for-duplicate-boilerplate-check", type=int, default=6, help="Minimum item count before duplicate boilerplate ratios are enforced.")
    parser.add_argument(
        "--forbidden-token",
        action="append",
        default=[],
        help="Run-specific forbidden token to search in final output; repeatable. No author-specific tokens are forbidden by default.",
    )
    return parser


def main() -> None:
    raise SystemExit(validate(build_parser().parse_args()))


if __name__ == "__main__":
    main()
