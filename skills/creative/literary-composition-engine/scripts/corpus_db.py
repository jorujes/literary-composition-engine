#!/usr/bin/env python3
"""Mechanical SQLite helper for authorial corpus preparation.

This script must not make editorial decisions. Agents decide what text belongs
in the corpus; this tool only persists, counts, lists, indexes, and reports.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sqlite3
from pathlib import Path
from typing import Any


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS stories (
  story_id    TEXT PRIMARY KEY,
  title       TEXT NOT NULL,
  collection  TEXT,
  source_file TEXT,
  pub_year    INTEGER,
  word_count  INTEGER,
  schema_v    INTEGER DEFAULT 1,
  ingested_at TEXT,
  UNIQUE(title, collection)
);

CREATE TABLE IF NOT EXISTS paragraphs (
  id          INTEGER PRIMARY KEY,
  story_id    TEXT REFERENCES stories(story_id) ON DELETE CASCADE,
  position    INTEGER NOT NULL,
  text        TEXT NOT NULL,
  UNIQUE(story_id, position)
);

CREATE TABLE IF NOT EXISTS sentences (
  sentence_id INTEGER PRIMARY KEY,
  paragraph_id INTEGER REFERENCES paragraphs(id) ON DELETE CASCADE,
  story_id    TEXT REFERENCES stories(story_id) ON DELETE CASCADE,
  paragraph_position INTEGER NOT NULL,
  sentence_position  INTEGER NOT NULL,
  text        TEXT NOT NULL,
  UNIQUE(paragraph_id, sentence_position)
);

CREATE TABLE IF NOT EXISTS ingestion_log (
  story_id    TEXT PRIMARY KEY,
  title       TEXT,
  collection  TEXT,
  source_file TEXT,
  pub_year    INTEGER,
  status      TEXT DEFAULT 'pending',
  confidence  REAL,
  reason      TEXT,
  updated_at  TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS paragraphs_fts USING fts5(
  text, content=paragraphs, content_rowid=id
);

CREATE VIRTUAL TABLE IF NOT EXISTS sentences_fts USING fts5(
  text, content=sentences, content_rowid=sentence_id
);
"""


WORD_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?…])\s+(?=[A-ZÀ-ÖØ-Þ0-9\"'“‘])", re.UNICODE)


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def word_count(paragraphs: list[str]) -> int:
    return sum(len(WORD_RE.findall(p)) for p in paragraphs)


def split_sentences(text: str) -> list[str]:
    """Mechanical sentence split for indexing; agents may repair source text before this runs."""
    parts = [part.strip() for part in SENTENCE_SPLIT_RE.split(text.strip())]
    return [part for part in parts if part]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def init_db(args: argparse.Namespace) -> None:
    with connect(args.db) as conn:
        conn.executescript(SCHEMA)
        migrate_schema(conn)
    print(f"initialized {args.db}")


def migrate_schema(conn: sqlite3.Connection) -> None:
    """Additive migrations for DBs created by earlier versions of this helper."""
    # The old `sentence_patterns` table is intentionally not created or migrated.
    # Phase 4 now uses real source sentences directly from `sentences`.
    return None


def load_manifest(args: argparse.Namespace) -> None:
    manifest = read_json(args.manifest)
    works = manifest.get("works", [])
    if not isinstance(works, list):
        raise SystemExit("manifest.works must be a list")

    with connect(args.db) as conn:
        conn.executescript(SCHEMA)
        migrate_schema(conn)
        for work in works:
            story_id = required_str(work, "story_id")
            conn.execute(
                """
                INSERT INTO ingestion_log (
                  story_id, title, collection, source_file, pub_year,
                  status, confidence, reason, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(story_id) DO UPDATE SET
                  title=excluded.title,
                  collection=excluded.collection,
                  source_file=excluded.source_file,
                  pub_year=excluded.pub_year,
                  status=excluded.status,
                  confidence=excluded.confidence,
                  reason=excluded.reason,
                  updated_at=excluded.updated_at
                """,
                (
                    story_id,
                    work.get("title"),
                    work.get("collection"),
                    work.get("source_file"),
                    work.get("pub_year"),
                    work.get("status", "pending"),
                    work.get("confidence"),
                    work.get("reason"),
                    now_iso(),
                ),
            )
    print(f"loaded {len(works)} manifest item(s) into {args.db}")


def ingest_story(args: argparse.Namespace) -> None:
    payload = read_json(args.story_json)
    story_id = required_str(payload, "story_id")
    title = required_str(payload, "title")
    paragraphs = payload.get("paragraphs")
    if not isinstance(paragraphs, list) or not all(isinstance(p, str) for p in paragraphs):
        raise SystemExit("story_json.paragraphs must be a list of strings")

    cleaned = [p.strip() for p in paragraphs if p and p.strip()]
    wc = word_count(cleaned)
    status = payload.get("status", "done")
    confidence = payload.get("confidence")
    reason = payload.get("reason")

    with connect(args.db) as conn:
        conn.executescript(SCHEMA)
        migrate_schema(conn)
        conn.execute("DELETE FROM paragraphs WHERE story_id = ?", (story_id,))
        conn.execute(
            """
            INSERT INTO stories (
              story_id, title, collection, source_file, pub_year,
              word_count, schema_v, ingested_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            ON CONFLICT(story_id) DO UPDATE SET
              title=excluded.title,
              collection=excluded.collection,
              source_file=excluded.source_file,
              pub_year=excluded.pub_year,
              word_count=excluded.word_count,
              ingested_at=excluded.ingested_at
            """,
            (
                story_id,
                title,
                payload.get("collection"),
                payload.get("source_file"),
                payload.get("pub_year"),
                wc,
                now_iso(),
            ),
        )
        conn.executemany(
            "INSERT INTO paragraphs (story_id, position, text) VALUES (?, ?, ?)",
            [(story_id, i + 1, text) for i, text in enumerate(cleaned)],
        )
        rebuild_sentences_for_story(conn, story_id)
        conn.execute(
            """
            INSERT INTO ingestion_log (
              story_id, title, collection, source_file, pub_year,
              status, confidence, reason, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(story_id) DO UPDATE SET
              title=excluded.title,
              collection=excluded.collection,
              source_file=excluded.source_file,
              pub_year=excluded.pub_year,
              status=excluded.status,
              confidence=excluded.confidence,
              reason=excluded.reason,
              updated_at=excluded.updated_at
            """,
            (
                story_id,
                title,
                payload.get("collection"),
                payload.get("source_file"),
                payload.get("pub_year"),
                status,
                confidence,
                reason,
                now_iso(),
            ),
        )
    print(f"ingested {story_id}: {len(cleaned)} paragraph(s), {wc} word(s), status={status}")


def rebuild_sentences_for_story(conn: sqlite3.Connection, story_id: str) -> None:
    conn.execute("DELETE FROM sentences WHERE story_id = ?", (story_id,))
    rows = conn.execute(
        """
        SELECT id, story_id, position, text
        FROM paragraphs
        WHERE story_id = ?
        ORDER BY position
        """,
        (story_id,),
    ).fetchall()
    sentence_rows = []
    for row in rows:
        for i, sentence in enumerate(split_sentences(row["text"]), 1):
            sentence_rows.append((row["id"], row["story_id"], row["position"], i, sentence))
    conn.executemany(
        """
        INSERT INTO sentences (
          paragraph_id, story_id, paragraph_position, sentence_position, text
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        sentence_rows,
    )


def rebuild_sentences(args: argparse.Namespace) -> None:
    with connect(args.db) as conn:
        conn.executescript(SCHEMA)
        migrate_schema(conn)
        story_ids = conn.execute("SELECT story_id FROM stories ORDER BY story_id").fetchall()
        for row in story_ids:
            rebuild_sentences_for_story(conn, row["story_id"])
        conn.execute("INSERT INTO sentences_fts(sentences_fts) VALUES('rebuild')")
    print(f"rebuilt sentence index for {args.db}: {len(story_ids)} story/stories")


def list_items(args: argparse.Namespace) -> None:
    with connect(args.db) as conn:
        conn.executescript(SCHEMA)
        migrate_schema(conn)
        rows = conn.execute(
            """
            SELECT story_id, title, status, confidence, reason
            FROM ingestion_log
            WHERE (? IS NULL OR status = ?)
            ORDER BY story_id
            """,
            (args.status, args.status),
        ).fetchall()
    for row in rows:
        print(json.dumps(dict(row), ensure_ascii=False))


def mark(args: argparse.Namespace) -> None:
    with connect(args.db) as conn:
        conn.executescript(SCHEMA)
        migrate_schema(conn)
        conn.execute(
            """
            UPDATE ingestion_log
            SET status = ?, confidence = COALESCE(?, confidence),
                reason = COALESCE(?, reason), updated_at = ?
            WHERE story_id = ?
            """,
            (args.status, args.confidence, args.reason, now_iso(), args.story_id),
        )
        if conn.total_changes == 0:
            raise SystemExit(f"story_id not found: {args.story_id}")
    print(f"marked {args.story_id} as {args.status}")


def rebuild_fts(args: argparse.Namespace) -> None:
    with connect(args.db) as conn:
        conn.executescript(SCHEMA)
        migrate_schema(conn)
        conn.execute("INSERT INTO paragraphs_fts(paragraphs_fts) VALUES('rebuild')")
        conn.execute("INSERT INTO sentences_fts(sentences_fts) VALUES('rebuild')")
    print(f"rebuilt FTS index for {args.db}")


def report(args: argparse.Namespace) -> None:
    with connect(args.db) as conn:
        conn.executescript(SCHEMA)
        migrate_schema(conn)
        story_count = conn.execute("SELECT COUNT(*) FROM stories").fetchone()[0]
        paragraph_count = conn.execute("SELECT COUNT(*) FROM paragraphs").fetchone()[0]
        sentence_count = conn.execute("SELECT COUNT(*) FROM sentences").fetchone()[0]
        total_words = conn.execute("SELECT COALESCE(SUM(word_count), 0) FROM stories").fetchone()[0]
        statuses = conn.execute(
            "SELECT status, COUNT(*) AS count FROM ingestion_log GROUP BY status ORDER BY status"
        ).fetchall()
        low_word = conn.execute(
            """
            SELECT story_id, title, word_count
            FROM stories
            WHERE word_count < ?
            ORDER BY word_count ASC
            """,
            (args.min_words,),
        ).fetchall()
    payload = {
        "db": str(args.db),
        "stories": story_count,
        "paragraphs": paragraph_count,
        "sentences": sentence_count,
        "words": total_words,
        "statuses": [dict(row) for row in statuses],
        "low_word_count": [dict(row) for row in low_word],
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def required_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"missing required string: {key}")
    return value.strip()


def required_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise SystemExit(f"missing required integer: {key}")
    return value


def required_list_json(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
        raise SystemExit(f"missing required non-empty string list: {key}")
    return json.dumps([item.strip() for item in value], ensure_ascii=False)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mechanical SQLite helper for authorial corpora")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init")
    p.add_argument("--db", type=Path, required=True)
    p.set_defaults(func=init_db)

    p = sub.add_parser("load-manifest")
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.set_defaults(func=load_manifest)

    p = sub.add_parser("ingest-story")
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--story-json", type=Path, required=True)
    p.set_defaults(func=ingest_story)

    p = sub.add_parser("rebuild-sentences")
    p.add_argument("--db", type=Path, required=True)
    p.set_defaults(func=rebuild_sentences)

    p = sub.add_parser("list")
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--status")
    p.set_defaults(func=list_items)

    p = sub.add_parser("mark")
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--story-id", required=True)
    p.add_argument("--status", choices=["pending", "done", "needs_review"], required=True)
    p.add_argument("--confidence", type=float)
    p.add_argument("--reason")
    p.set_defaults(func=mark)

    p = sub.add_parser("rebuild-fts")
    p.add_argument("--db", type=Path, required=True)
    p.set_defaults(func=rebuild_fts)

    p = sub.add_parser("report")
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--min-words", type=int, default=300)
    p.set_defaults(func=report)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
