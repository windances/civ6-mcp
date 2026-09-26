"""Build and query the local knowledge base (SQLite FTS5) from the command line.

    python .tools/kb.py index                          # prompts/, docs/, AGENTS.md, SETUP-WINDOWS.md
                                                       # + the extracted manual + .tools/kb/extra-sources.txt
    python .tools/kb.py index --source .tools/manuals/manual.clean.txt   # --source REPLACES the corpus
    python .tools/kb.py search "how does a city heal" -k 3
    python .tools/kb.py search "城墙" --doc manual
    python .tools/kb.py stats

The same index is what the `search_knowledge` MCP tool reads, so an in-game session can query the
manual mid-turn. Nothing here needs network, a model or a server: it is one SQLite file, and the
venv's SQLite (3.49.1) has FTS5 compiled in.

Index location: `--db`, else `$CIV_MCP_KNOWLEDGE_DB`, else `.tools/kb/knowledge.sqlite` in the
current checkout. Rebuild it in each checkout you play from (a game clone has its own), and after
the corpus changes - a stale index answers confidently with text that no longer exists.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from civ_mcp import knowledge  # noqa: E402


def cmd_index(args: argparse.Namespace) -> int:
    sources = tuple(args.source) if args.source else knowledge.default_sources()
    summary = knowledge.build(sources, db=args.db)
    print(
        f"indexed {summary['docs']} document(s), {summary['chunks']} chunk(s) -> {summary['db']}"
    )
    extras = knowledge.extra_sources()
    if extras and not args.source:
        print(f"local extra sources ({knowledge.EXTRA_SOURCES_FILE}): {', '.join(extras)}")
    missing = [str(s) for s in sources if not pathlib.Path(s).exists()]
    if missing:
        print(f"note: source(s) not found and skipped: {', '.join(missing)}")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    hits = knowledge.search(args.query, k=args.k, doc=args.doc, db=args.db)
    print(knowledge.format_hits(hits, args.query))
    return 0 if hits else 1


def cmd_stats(args: argparse.Namespace) -> int:
    info = knowledge.stats(db=args.db)
    if not info["exists"]:
        print(knowledge.build_hint())
        return 1
    print(f"index: {info['db']}")
    print(f"documents: {info['docs']} (largest shown), chunks: {info['chunks']}")
    for doc, count in info["top"]:
        print(f"  {count:>5} chunks  {doc}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    index = sub.add_parser("index", help="rebuild the index")
    index.add_argument("--source", action="append", help="file or directory (repeatable)")
    index.add_argument("--db")
    index.set_defaults(func=cmd_index)

    search = sub.add_parser("search", help="query the index")
    search.add_argument("query")
    search.add_argument("-k", type=int, default=5)
    search.add_argument("--doc", help="only docs whose path contains this")
    search.add_argument("--db")
    search.set_defaults(func=cmd_search)

    stats = sub.add_parser("stats", help="what is indexed")
    stats.add_argument("--db")
    stats.set_defaults(func=cmd_stats)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
