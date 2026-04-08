#!/usr/bin/env python3
"""
Document Registry Inspection Tool

CLI tool to inspect and query the Document Registry SQLite database.

Usage:
    uv run python scripts/inspect_registry.py list [--user-id USER_ID] [--collection COLLECTION]
    uv run python scripts/inspect_registry.py search-author "Author Name" [--user-id USER_ID]
    uv run python scripts/inspect_registry.py search-title "Title" [--user-id USER_ID]
    uv run python scripts/inspect_registry.py get DOC_ID
    uv run python scripts/inspect_registry.py stats [--user-id USER_ID]
    uv run python scripts/inspect_registry.py types [--user-id USER_ID]
    uv run python scripts/inspect_registry.py raw-sql "SELECT * FROM documents LIMIT 5"
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import settings
from backend.retrieval.schema.registry import DocumentRegistry


def get_registry_path(user_id: str) -> str:
    """Get path to user's document registry database."""
    # Registries are stored INSIDE chroma_db for Docker volume persistence
    registry_dir = os.path.join(settings.CHROMA_PERSIST_DIRECTORY, "registries")
    return os.path.join(registry_dir, user_id, "document_registry.db")


def find_all_registries() -> list:
    """Find all user registries."""
    registry_dir = os.path.join(settings.CHROMA_PERSIST_DIRECTORY, "registries")
    if not os.path.exists(registry_dir):
        return []

    registries = []
    for user_id in os.listdir(registry_dir):
        db_path = os.path.join(registry_dir, user_id, "document_registry.db")
        if os.path.exists(db_path):
            registries.append((user_id, db_path))
    return registries


def format_document(doc: dict, verbose: bool = False) -> str:
    """Format a document for display."""
    lines = []
    lines.append(f"  ID: {doc.get('doc_id', 'N/A')}")
    title = doc.get('title', 'N/A') or 'N/A'
    lines.append(f"  Title: {title}")  # Full title, no truncation
    lines.append(f"  Authors: {', '.join(doc.get('authors', [])) or 'N/A'}")
    lines.append(f"  Type: {doc.get('doc_type', 'N/A')}")
    lines.append(f"  File: {doc.get('file_name', 'N/A')}")

    if verbose:
        lines.append(f"  Path: {doc.get('file_path', 'N/A')}")
        lines.append(f"  Pages: {doc.get('page_count', 'N/A')}")
        lines.append(f"  Collection: {doc.get('collection_name', 'N/A')}")
        lines.append(f"  Has Abstract: {doc.get('has_abstract', False)}")
        lines.append(f"  Has Tables: {doc.get('has_tables', False)}")
        lines.append(f"  Has Figures: {doc.get('has_figures', False)}")
        if doc.get('sections'):
            lines.append(f"  Sections: {', '.join(doc.get('sections', []))[:100]}")
        lines.append(f"  Created: {doc.get('created_at', 'N/A')}")

    return '\n'.join(lines)


def cmd_list(args):
    """List all documents."""
    if args.user_id:
        registries = [(args.user_id, get_registry_path(args.user_id))]
    else:
        registries = find_all_registries()

    if not registries:
        print("No registries found.")
        return

    for user_id, db_path in registries:
        if not os.path.exists(db_path):
            print(f"Registry not found for user: {user_id}")
            continue

        print(f"\n{'='*60}")
        print(f"User: {user_id}")
        print(f"Registry: {db_path}")
        print(f"{'='*60}")

        registry = DocumentRegistry(db_path)
        docs = registry.get_all_documents(
            collection_name=args.collection,
            limit=args.limit
        )

        if not docs:
            print("  No documents found.")
            continue

        print(f"  Found {len(docs)} document(s):\n")
        for i, doc in enumerate(docs, 1):
            print(f"[{i}]")
            print(format_document(doc, verbose=args.verbose))
            print()


def cmd_search_author(args):
    """Search documents by author."""
    if args.user_id:
        registries = [(args.user_id, get_registry_path(args.user_id))]
    else:
        registries = find_all_registries()

    for user_id, db_path in registries:
        if not os.path.exists(db_path):
            continue

        print(f"\nSearching in user: {user_id}")
        registry = DocumentRegistry(db_path)
        docs = registry.get_by_author(args.author_name)

        if not docs:
            print(f"  No documents found for author: {args.author_name}")
            continue

        print(f"  Found {len(docs)} document(s) by '{args.author_name}':\n")
        for i, doc in enumerate(docs, 1):
            print(f"[{i}]")
            print(format_document(doc, verbose=args.verbose))
            print()


def cmd_search_title(args):
    """Search documents by title."""
    if args.user_id:
        registries = [(args.user_id, get_registry_path(args.user_id))]
    else:
        registries = find_all_registries()

    for user_id, db_path in registries:
        if not os.path.exists(db_path):
            continue

        print(f"\nSearching in user: {user_id}")
        registry = DocumentRegistry(db_path)
        docs = registry.search_title(args.title_query)

        if not docs:
            print(f"  No documents found matching: {args.title_query}")
            continue

        print(f"  Found {len(docs)} document(s) matching '{args.title_query}':\n")
        for i, doc in enumerate(docs, 1):
            print(f"[{i}]")
            print(format_document(doc, verbose=args.verbose))
            print()


def cmd_get(args):
    """Get a specific document by ID."""
    registries = find_all_registries()

    for user_id, db_path in registries:
        if not os.path.exists(db_path):
            continue

        registry = DocumentRegistry(db_path)
        doc = registry.get_document(args.doc_id)

        if doc:
            print(f"\nDocument found in user: {user_id}\n")
            print(format_document(doc, verbose=True))

            # Show full JSON if requested
            if args.json:
                print("\nFull JSON:")
                print(json.dumps(doc, indent=2, default=str))
            return

    print(f"Document not found: {args.doc_id}")


def cmd_stats(args):
    """Show statistics for the registry."""
    if args.user_id:
        registries = [(args.user_id, get_registry_path(args.user_id))]
    else:
        registries = find_all_registries()

    for user_id, db_path in registries:
        if not os.path.exists(db_path):
            continue

        print(f"\n{'='*60}")
        print(f"User: {user_id}")
        print(f"{'='*60}")

        registry = DocumentRegistry(db_path)
        stats = registry.get_stats()

        print(f"  Total Documents: {stats.get('total_documents', 0)}")
        print(f"  Unique Authors: {stats.get('unique_authors', 0)}")

        print("\n  Documents by Type:")
        for doc_type, count in stats.get('by_type', {}).items():
            print(f"    {doc_type}: {count}")


def cmd_types(args):
    """List documents by type."""
    if args.user_id:
        registries = [(args.user_id, get_registry_path(args.user_id))]
    else:
        registries = find_all_registries()

    for user_id, db_path in registries:
        if not os.path.exists(db_path):
            continue

        print(f"\nUser: {user_id}")
        registry = DocumentRegistry(db_path)

        if args.type:
            docs = registry.get_by_type(args.type)
            print(f"  {args.type}: {len(docs)} document(s)")
            for doc in docs[:10]:  # Limit to 10
                print(f"    - {doc.get('title', doc.get('file_name', 'N/A'))[:60]}")
        else:
            stats = registry.get_stats()
            for doc_type, count in stats.get('by_type', {}).items():
                print(f"  {doc_type}: {count}")


def cmd_raw_sql(args):
    """Execute raw SQL query."""
    if not args.user_id:
        print("Error: --user-id is required for raw SQL queries")
        return

    db_path = get_registry_path(args.user_id)
    if not os.path.exists(db_path):
        print(f"Registry not found: {db_path}")
        return

    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        cursor = conn.execute(args.sql)
        rows = cursor.fetchall()

        if not rows:
            print("No results.")
            return

        # Print as table
        columns = [desc[0] for desc in cursor.description]
        print(" | ".join(columns))
        print("-" * (len(" | ".join(columns))))

        for row in rows:
            values = [str(row[col])[:50] for col in columns]
            print(" | ".join(values))

        print(f"\n({len(rows)} rows)")

    except Exception as e:
        print(f"SQL Error: {e}")
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Document Registry Inspection Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List all documents")
    list_parser.add_argument("--user-id", help="Filter by user ID")
    list_parser.add_argument("--collection", help="Filter by collection name")
    list_parser.add_argument("--limit", type=int, default=100, help="Max documents to show")
    list_parser.add_argument("-v", "--verbose", action="store_true", help="Show full details")

    # Search author command
    author_parser = subparsers.add_parser("search-author", help="Search by author name")
    author_parser.add_argument("author_name", help="Author name to search")
    author_parser.add_argument("--user-id", help="Filter by user ID")
    author_parser.add_argument("-v", "--verbose", action="store_true", help="Show full details")

    # Search title command
    title_parser = subparsers.add_parser("search-title", help="Search by title")
    title_parser.add_argument("title_query", help="Title to search")
    title_parser.add_argument("--user-id", help="Filter by user ID")
    title_parser.add_argument("-v", "--verbose", action="store_true", help="Show full details")

    # Get command
    get_parser = subparsers.add_parser("get", help="Get document by ID")
    get_parser.add_argument("doc_id", help="Document ID")
    get_parser.add_argument("--json", action="store_true", help="Output full JSON")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show registry statistics")
    stats_parser.add_argument("--user-id", help="Filter by user ID")

    # Types command
    types_parser = subparsers.add_parser("types", help="List documents by type")
    types_parser.add_argument("--user-id", help="Filter by user ID")
    types_parser.add_argument("--type", help="Filter by specific type (PAPER, GRANT, etc.)")

    # Raw SQL command
    sql_parser = subparsers.add_parser("raw-sql", help="Execute raw SQL query")
    sql_parser.add_argument("sql", help="SQL query to execute")
    sql_parser.add_argument("--user-id", required=True, help="User ID (required)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    commands = {
        "list": cmd_list,
        "search-author": cmd_search_author,
        "search-title": cmd_search_title,
        "get": cmd_get,
        "stats": cmd_stats,
        "types": cmd_types,
        "raw-sql": cmd_raw_sql,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
