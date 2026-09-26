"""A local knowledge base the agent can query *during* a turn: SQLite FTS5 over text files.

Why this exists: the agent only knows what it queries, and a good part of what decides a turn is
reference material rather than game state - the Civ VI manual, the strategy directive, the rule
file, the retrospectives. Reading the manual (557 KB of text) into a turn is not an option;
asking it a question is. This is deliberately the smallest thing that works:

* one SQLite file, **FTS5** (BM25 ranking, `snippet()` context, phrase/prefix queries);
* **no embeddings, no vector DB, no network, no new dependency** - this venv's SQLite is 3.49.1
  with `fts5` compiled in, which was checked before any of this was written;
* chunks carry `doc` + `start_line`/`end_line`, so a hit can be read in full with `read` and cited
  as evidence instead of paraphrased.

Build it with `.tools/kb.py index` (or :func:`build`); query it with `.tools/kb.py search` or the
`search_knowledge` MCP tool, which is what an in-game session actually calls mid-turn.

The index lives at ``$CIV_MCP_KNOWLEDGE_DB`` or ``<cwd>/.tools/kb/knowledge.sqlite``, i.e. per
checkout - a game clone needs its own copy (the corpus is local files, and the manual is
copyrighted, so it is never committed).

Chinese queries fall back to ``LIKE``: the default ``unicode61`` tokenizer does not split CJK into
words, and the ``trigram`` tokenizer is not compiled into this SQLite build (checked).
"""

from __future__ import annotations

import os
import pathlib
import re
import sqlite3
from dataclasses import dataclass

# What gets indexed when no sources are named. `src/` is deliberately not here: the manual and the
# prompts are what a turn needs to look up, the code is already searchable with grep.
# The corpus `python .tools/kb.py index` builds. `.tools` is not skipped (see `_SKIP_DIRS`) precisely
# so the extracted game manual can live here: without it the index holds only our own writing, and the
# one question the doctrine cannot answer - "what does the manual actually say?" - has nowhere to go.
# `kb.py index --source` *replaces* this tuple rather than adding to it, so the manual belongs in the
# default set; a source that is absent (a fresh clone without `.tools/manuals/`) is skipped by
# `iter_files`, not an error.
DEFAULT_SOURCES = (
    "prompts",
    "docs",
    "AGENTS.md",
    "SETUP-WINDOWS.md",
    ".tools/manuals/manual.clean.txt",
)
DEFAULT_DB = ".tools/kb/knowledge.sqlite"

_TEXT_SUFFIXES = (".md", ".txt", ".yml", ".yaml", ".json")
# Directories that are never part of a corpus. `.tools` is deliberately *not* here: the extracted
# manual lives in `.tools/manuals/`, and the sandbox only lets tests write under `.tools/`, so
# skipping it would make the index unbuildable exactly where it is needed.
_SKIP_DIRS = {
    ".git", ".venv", "node_modules", "__pycache__", ".civ6-mcp-data",
    ".dsh-home", ".mypy_cache", ".pytest_cache", "archive",
}
_CHUNK_CHARS = 1200
_MAX_TEXT_CHARS = 400_000  # a single huge file (a log dump) would drown the index
_HEADING = re.compile(r"^\s{0,3}#{1,4}\s+(.*\S)\s*$")
_PAGE_NUMBER = re.compile(r"^\s*(\d{1,4})\s*$")
_CAPS_HEADING = re.compile(r"^\s*([A-Z][A-Z0-9 ,:&'()/-]{6,60})\s*$")


@dataclass
class Hit:
    """One chunk that matched, with enough to read and cite it."""

    doc: str
    section: str
    start_line: int
    end_line: int
    snippet: str
    score: float


def db_path(explicit: str | pathlib.Path | None = None) -> pathlib.Path:
    """Where the index lives: explicit, else $CIV_MCP_KNOWLEDGE_DB, else <cwd>/.tools/kb/…"""
    if explicit:
        return pathlib.Path(explicit)
    configured = os.environ.get("CIV_MCP_KNOWLEDGE_DB")
    if configured:
        return pathlib.Path(configured)
    return pathlib.Path(DEFAULT_DB)


def _rel(path: pathlib.Path) -> str:
    try:
        return path.relative_to(pathlib.Path.cwd()).as_posix()
    except ValueError:
        return path.as_posix()


def iter_files(sources) -> list[pathlib.Path]:
    """Every indexable text file under the given files/directories, in a stable order."""
    found: list[pathlib.Path] = []
    for source in sources:
        path = pathlib.Path(source)
        if path.is_file():
            found.append(path)
            continue
        if not path.is_dir():
            continue
        for child in sorted(path.rglob("*")):
            if not child.is_file() or child.suffix.lower() not in _TEXT_SUFFIXES:
                continue
            if any(part in _SKIP_DIRS for part in child.parts):
                continue
            found.append(child)
    # De-duplicate while keeping order (a file named twice in sources is indexed once).
    seen: set[pathlib.Path] = set()
    unique: list[pathlib.Path] = []
    for path in found:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(path)
    return unique


def _heading_of(line: str, previous: str) -> str:
    """The section a line belongs to: a markdown heading, an ALL-CAPS title, or a page number."""
    stripped = line.strip()
    if not stripped:
        return previous
    markdown = _HEADING.match(line)
    if markdown:
        return markdown.group(1)[:80]
    page = _PAGE_NUMBER.match(line)
    if page:
        return f"p{page.group(1)}"
    caps = _CAPS_HEADING.match(line)
    if caps and len(caps.group(1).split()) >= 2:
        return caps.group(1).strip()[:80]
    return previous


def chunk_text(text: str) -> list[tuple[int, int, str, str]]:
    """(start_line, end_line, section, chunk) tuples: paragraph groups up to ``_CHUNK_CHARS``.

    Chunks follow paragraph breaks rather than a fixed window, so a retrieved piece is a whole
    thought; the line numbers are the chunk's own extent in the source file, which is what makes
    the hit citable and re-readable.
    """
    lines = text.splitlines()
    chunks: list[tuple[int, int, str, str]] = []
    buffer: list[str] = []
    start = 1
    section = ""
    chunk_section = ""

    def flush(end_line: int) -> None:
        nonlocal buffer
        if any(part.strip() for part in buffer):
            body = "\n".join(buffer).strip()
            if body:
                chunks.append((start, end_line, chunk_section, body))
        buffer = []

    for number, line in enumerate(lines, start=1):
        section = _heading_of(line, section)
        if not buffer:
            start = number
            # The section the chunk *starts* in, not the last heading it happens to run into.
            chunk_section = section
        buffer.append(line)
        if len("\n".join(buffer)) >= _CHUNK_CHARS:
            flush(number)
    flush(len(lines))
    return chunks


def connect(db: str | pathlib.Path | None = None) -> sqlite3.Connection:
    path = db_path(db)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5("
        "doc UNINDEXED, section UNINDEXED, start_line UNINDEXED, end_line UNINDEXED, text,"
        " tokenize = 'unicode61 remove_diacritics 2')"
    )
    return con


def build(
    sources=DEFAULT_SOURCES,
    db: str | pathlib.Path | None = None,
    extra_texts: dict | None = None,
) -> dict:
    """(Re)build the index over ``sources`` (plus ``{name: text}`` extras). Returns a summary."""
    path = db_path(db)
    if path.exists():
        path.unlink()  # a rebuild, not an append: stale chunks are worse than none
    con = connect(path)
    docs = 0
    chunks = 0
    try:
        for file in iter_files(sources):
            try:
                text = file.read_text(encoding="utf-8-sig", errors="replace")
            except OSError:
                continue
            if not text.strip() or len(text) > _MAX_TEXT_CHARS:
                continue
            rows = chunk_text(text)
            if not rows:
                continue
            con.executemany(
                "INSERT INTO chunks (doc, section, start_line, end_line, text)"
                " VALUES (?, ?, ?, ?, ?)",
                [(_rel(file), section, start, end, body) for start, end, section, body in rows],
            )
            docs += 1
            chunks += len(rows)
        for name, text in (extra_texts or {}).items():
            rows = chunk_text(text)
            con.executemany(
                "INSERT INTO chunks (doc, section, start_line, end_line, text)"
                " VALUES (?, ?, ?, ?, ?)",
                [(name, section, start, end, body) for start, end, section, body in rows],
            )
            docs += 1
            chunks += len(rows)
        con.commit()
    finally:
        con.close()
    return {"db": str(path), "docs": docs, "chunks": chunks}


def _fts_query(query: str) -> str:
    """A safe FTS5 MATCH expression: every token quoted, joined with OR (BM25 still ranks)."""
    tokens = [token for token in re.split(r"[^\w\u4e00-\u9fff]+", query) if token]
    if not tokens:
        return ""
    return " OR ".join(f'"{token}"' for token in tokens)


def _has_cjk(query: str) -> bool:
    return any("\u3400" <= char <= "\u9fff" for char in query)


def search(
    query: str,
    k: int = 5,
    doc: str | None = None,
    db: str | pathlib.Path | None = None,
) -> list[Hit]:
    """Top-``k`` chunks for ``query``, optionally restricted to docs whose path contains ``doc``.

    Returns an empty list when the index does not exist yet or nothing matches - the caller (an
    agent) gets a real answer either way, and :func:`build_hint` says how to fix the first case.
    """
    path = db_path(db)
    if not path.exists() or not query.strip():
        return []
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        if _has_cjk(query) and not _fts_query(query):
            return []
        if _has_cjk(query):
            return _search_like(con, query, k, doc)
        match = _fts_query(query)
        if not match:
            return []
        where = "chunks MATCH ?"
        params: list = [match]
        if doc:
            where += " AND doc LIKE ?"
            params.append(f"%{doc}%")
        params.append(max(1, min(int(k), 25)))
        rows = con.execute(
            "SELECT doc, section, start_line, end_line,"
            " snippet(chunks, 4, '[', ']', ' … ', 14), bm25(chunks) "
            f"FROM chunks WHERE {where} ORDER BY bm25(chunks) LIMIT ?",
            params,
        ).fetchall()
        return [
            Hit(str(row[0]), str(row[1]), int(row[2]), int(row[3]), str(row[4]), float(row[5]))
            for row in rows
        ]
    except sqlite3.Error:
        return _search_like(con, query, k, doc)
    finally:
        con.close()


def _terms(query: str) -> list[str]:
    """Search terms for the LIKE fallback: CJK runs (>=2 chars) and latin words alike."""
    cjk = [run for run in re.findall(r"[\u3400-\u9fff]{2,}", query)]
    words = [word for word in re.split(r"[^\w\u3400-\u9fff]+", query) if len(word) >= 2]
    seen: set[str] = set()
    terms: list[str] = []
    for term in cjk + words:
        if term.lower() in seen:
            continue
        seen.add(term.lower())
        terms.append(term)
    return terms


def _search_like(con: sqlite3.Connection, query: str, k: int, doc: str | None) -> list[Hit]:
    """CJK (and malformed-FTS) fallback: substring match, ranked by how many terms hit.

    `unicode61` does not split Chinese into words and this SQLite build has no `trigram`
    tokenizer, so a CJK query has no tokens for FTS to match. Substring matching on the same
    chunks is the honest substitute, and ranking by term coverage puts a passage that contains
    most of the question above one that contains a single word of it.
    """
    terms = _terms(query)
    if not terms:
        return []
    where = "(" + " OR ".join("text LIKE ?" for _ in terms) + ")"
    params: list = [f"%{term}%" for term in terms]
    if doc:
        where += " AND doc LIKE ?"
        params.append(f"%{doc}%")
    params.append(max(1, min(int(k), 25)) * 4)  # over-fetch, then rank by coverage
    try:
        rows = con.execute(
            "SELECT doc, section, start_line, end_line, text, 0.0 FROM chunks "
            f"WHERE {where} LIMIT ?",
            params,
        ).fetchall()
    except sqlite3.Error:
        return []
    scored: list[tuple[int, int, tuple]] = []
    for row in rows:
        text = str(row[4])
        lowered = text.lower()
        present = [term for term in terms if term.lower() in lowered]
        if not present:
            continue
        at = min(lowered.find(term.lower()) for term in present)
        scored.append((-len(present), at if at >= 0 else 0, row))
    scored.sort(key=lambda item: (item[0], item[1]))
    hits: list[Hit] = []
    for coverage, _at, row in scored[: max(1, min(int(k), 25))]:
        text = str(row[4])
        first = min(
            (text.lower().find(term.lower()) for term in terms if term.lower() in text.lower()),
            default=0,
        )
        snippet = text[max(0, first - 120) : first + 240].replace("\n", " ")
        hits.append(
            Hit(
                str(row[0]),
                str(row[1]),
                int(row[2]),
                int(row[3]),
                f"…{snippet}… ({-coverage}/{len(terms)} terms)",
                0.0,
            )
        )
    return hits


def stats(db: str | pathlib.Path | None = None) -> dict:
    """What is indexed: documents, chunks, and the largest ones."""
    path = db_path(db)
    if not path.exists():
        return {"db": str(path), "exists": False, "docs": 0, "chunks": 0, "top": []}
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        chunks = con.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        rows = con.execute(
            "SELECT doc, COUNT(*) FROM chunks GROUP BY doc ORDER BY COUNT(*) DESC LIMIT 10"
        ).fetchall()
    except sqlite3.Error:
        return {"db": str(path), "exists": True, "docs": 0, "chunks": 0, "top": []}
    finally:
        con.close()
    top = [(str(row[0]), int(row[1])) for row in rows]
    return {
        "db": str(path),
        "exists": True,
        "docs": len(top),
        "chunks": int(chunks),
        "top": top,
    }


def build_hint() -> str:
    """The one line an agent needs when the index is missing."""
    return (
        f"knowledge index not found at {db_path()} - build it with "
        f"`python .tools/kb.py index` (add `--source <path>` for extra documents, e.g. the manual)"
    )


def format_hits(hits: list[Hit], query: str, db: str | pathlib.Path | None = None) -> str:
    """The tool's answer: every hit with its source, line range and a highlighted snippet."""
    if hits:
        lines = [
            f"KNOWLEDGE: {len(hits)} match(es) for {query!r} "
            "(read the source lines for the full text):"
        ]
        for hit in hits:
            where = f"{hit.doc}:{hit.start_line}-{hit.end_line}"
            section = f" [{hit.section}]" if hit.section else ""
            lines.append(f"  {where}{section}\n    {hit.snippet}")
        return "\n".join(lines)
    # Distinguish "nothing matched" from "there is no index": the first is an answer, the second
    # is a setup problem, and telling an agent the wrong one wastes its next action.
    if not db_path(db).exists():
        return f"No knowledge-base match for {query!r}. {build_hint()}"
    return (
        f"No knowledge-base match for {query!r} in the index at {db_path(db)} - "
        "try fewer or different words, or drop `doc` to search everything."
    )
