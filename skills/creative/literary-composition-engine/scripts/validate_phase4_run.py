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
    "sentence_anchor.matching.yaml",
    "source_sentence_anchor.selection.yaml",
    "paragraph.rewrite.plan.yaml",
    "candidate.output.yaml",
    "audit.report.yaml",
    "sentence_anchor.final_audit.yaml",
    "final.anchor.lock.yaml",
    "final.paragraph.yaml",
    "paragraph.release.yaml",
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

FORMAL_MATCH_CHECK_KEYS = [
    "mood_match",
    "clause_sequence_match",
    "coordination_subordination_match",
    "turn_logic_match",
    "punctuation_function_match",
    "category_fit",
]

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


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\wÀ-ÖØ-öø-ÿ]+\b", text or ""))


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
        counts[value] = counts.get(value, 0) + 1
    return max(counts.values()) / len(cleaned)


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

    paragraph_count = args.paragraph_count
    released_count = 0
    sentence_mapping_count = 0
    final_texts: list[str] = []
    all_source_refs: list[Any] = []
    all_source_fidelity: list[str] = []
    all_semantic_independence: list[str] = []
    all_selection_reasons: list[str] = []
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

        neutral = artifact_root(loaded.get("neutral.paragraph.yaml"), "neutral_paragraph")
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
                if not isinstance(candidates, list) or len(candidates) < 3:
                    finding(
                        "sentence_anchor_matching_too_few_candidates",
                        pdir / "sentence_anchor.matching.yaml",
                        f"{pid}/{sentence_id or '?'} must record at least three form-matching candidates",
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
                if missing_or_empty(item.get("why_selected_before_writing")):
                    finding(
                        "sentence_anchor_matching_missing_prewrite_reason",
                        pdir / "sentence_anchor.matching.yaml",
                        f"{pid}/{sentence_id or '?'} lacks why_selected_before_writing",
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
                        if value not in {"yes", "acceptable_difference"}:
                            finding(
                                "sentence_anchor_formal_match_check_failed",
                                pdir / "sentence_anchor.final_audit.yaml",
                                f"{pid}/{sentence_id} formal_match_checks.{key} is {value!r}",
                            )
                if result.get("initial_anchor_status") in {"weak_anchor", "failed_anchor"}:
                    repair_required = True
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
        if candidate_text and final_text and candidate_text.strip() != final_text.strip():
            finding(
                "locked_candidate_differs_from_final_paragraph",
                pdir / locked_candidate_ref,
                f"{pid} locked candidate text does not match final.paragraph.yaml",
            )
        neutral_plain = normalize_prose(strip_neutral_stub_labels(neutral_text))
        candidate_plain = normalize_prose(candidate_text)
        final_plain = normalize_prose(final_text)
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
                if missing_or_empty(item.get("selected_source_form_analysis")):
                    finding(
                        "source_anchor_selection_missing_source_form_analysis",
                        pdir / "source_sentence_anchor.selection.yaml",
                        f"{pid}/{sentence_id or '?'} lacks selected_source_form_analysis",
                    )
                if not item.get("selected_source_sentence_text"):
                    finding(
                        "missing_selected_source_sentence_text",
                        pdir / "source_sentence_anchor.selection.yaml",
                        f"{pid}/{sentence_id or '?'} lacks selected_source_sentence_text",
                    )
                if not isinstance(item.get("candidate_source_sentences_considered"), list) or len(item.get("candidate_source_sentences_considered") or []) < 2:
                    finding(
                        "missing_rejected_source_sentence_candidates",
                        pdir / "source_sentence_anchor.selection.yaml",
                        f"{pid}/{sentence_id or '?'} must record multiple candidate source sentences considered",
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
                source_parts = item.get("source_sentence_parts")
                if not isinstance(source_parts, list) or not source_parts:
                    finding(
                        "source_anchor_selection_missing_source_parts",
                        pdir / "source_sentence_anchor.selection.yaml",
                        f"{pid}/{sentence_id or '?'} lacks source_sentence_parts",
                    )
                else:
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
                        if missing_or_empty(part.get("formal_job")) or is_generic_source_span(part.get("formal_job")):
                            finding(
                                "source_anchor_selection_generic_formal_job",
                                pdir / "source_sentence_anchor.selection.yaml",
                                f"{pid}/{sentence_id or '?'} has generic formal_job: {part.get('formal_job')!r}",
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
                        if missing_or_empty(part_map.get("source_formal_job")) or is_generic_source_span(part_map.get("source_formal_job")):
                            finding(
                                "source_alignment_generic_formal_job",
                                pdir / "source_sentence_anchor.selection.yaml",
                                f"{pid}/{item.get('sentence_id', '?')} alignment has generic source_formal_job: {part_map.get('source_formal_job')!r}",
                            )
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
                for regex, label in SURFACE_GPTISM_PATTERNS:
                    if output_sentence and regex.search(output_sentence):
                        selection_entry = selection_entries.get(str(mapping.get("sentence_id")))
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
        generic_hits = [
            marker
            for marker in GENERIC_ALIGNMENT_MARKERS
            if marker.lower() in " ".join(all_source_fidelity + all_semantic_independence + all_selection_reasons).lower()
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
