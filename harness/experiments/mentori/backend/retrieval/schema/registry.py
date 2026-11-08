"""
Document Registry - SQLite database for fast metadata queries.

Separate from vector store. Enables queries like:
- "Find all papers by author X"
- "List all grants from 2023"
- "Show meeting notes with action items"
"""

import sqlite3
import json
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from contextlib import contextmanager

from backend.retrieval.schema.document import DocumentMetadata, DocumentType

logger = logging.getLogger(__name__)


class DocumentRegistry:
    """
    SQLite-based document registry for fast metadata queries.

    Design:
    - One registry per user (stored in user's data directory)
    - Separate table for documents and author variants
    - Full-text search on title and searchable_text
    """

    def __init__(self, db_path: str):
        """
        Initialize registry.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._ensure_tables()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _ensure_tables(self):
        """Create tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Main documents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    doc_id TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_hash TEXT,
                    doc_type TEXT NOT NULL,
                    title TEXT,
                    date TEXT,
                    page_count INTEGER DEFAULT 0,
                    has_abstract INTEGER DEFAULT 0,
                    has_tables INTEGER DEFAULT 0,
                    has_figures INTEGER DEFAULT 0,
                    searchable_text TEXT,
                    collection_name TEXT,
                    user_id TEXT,
                    type_metadata TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    -- VLM extraction fields (added in v2)
                    vlm_model TEXT,
                    extraction_confidence REAL,
                    figure_count INTEGER DEFAULT 0,
                    table_count INTEGER DEFAULT 0,
                    reference_count INTEGER DEFAULT 0,
                    figures_json TEXT,
                    tables_json TEXT,
                    references_json TEXT
                )
            ''')

            # Migrate existing tables to add new columns
            self._migrate_add_vlm_columns(cursor)

            # Authors table (many-to-many)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS document_authors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id TEXT NOT NULL,
                    author_name TEXT NOT NULL,
                    is_variant INTEGER DEFAULT 0,
                    FOREIGN KEY (doc_id) REFERENCES documents (doc_id) ON DELETE CASCADE
                )
            ''')

            # Sections table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS document_sections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id TEXT NOT NULL,
                    section_name TEXT NOT NULL,
                    section_order INTEGER,
                    FOREIGN KEY (doc_id) REFERENCES documents (doc_id) ON DELETE CASCADE
                )
            ''')

            # Indexes for fast queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_doc_type ON documents (doc_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_collection ON documents (collection_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user ON documents (user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_author ON document_authors (author_name COLLATE NOCASE)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_author_doc ON document_authors (doc_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_title ON documents (title COLLATE NOCASE)')

            # Full-text search virtual table
            cursor.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                    doc_id,
                    title,
                    searchable_text,
                    content='documents',
                    content_rowid='rowid'
                )
            ''')

            # Triggers to keep FTS in sync
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
                    INSERT INTO documents_fts(rowid, doc_id, title, searchable_text)
                    VALUES (new.rowid, new.doc_id, new.title, new.searchable_text);
                END
            ''')

            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
                    INSERT INTO documents_fts(documents_fts, rowid, doc_id, title, searchable_text)
                    VALUES('delete', old.rowid, old.doc_id, old.title, old.searchable_text);
                END
            ''')

            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
                    INSERT INTO documents_fts(documents_fts, rowid, doc_id, title, searchable_text)
                    VALUES('delete', old.rowid, old.doc_id, old.title, old.searchable_text);
                    INSERT INTO documents_fts(rowid, doc_id, title, searchable_text)
                    VALUES (new.rowid, new.doc_id, new.title, new.searchable_text);
                END
            ''')

    def _migrate_add_vlm_columns(self, cursor):
        """Add VLM extraction columns to existing databases."""
        # Check existing columns
        cursor.execute("PRAGMA table_info(documents)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        # New columns to add
        new_columns = [
            ("vlm_model", "TEXT"),
            ("extraction_confidence", "REAL"),
            ("figure_count", "INTEGER DEFAULT 0"),
            ("table_count", "INTEGER DEFAULT 0"),
            ("reference_count", "INTEGER DEFAULT 0"),
            ("figures_json", "TEXT"),
            ("tables_json", "TEXT"),
            ("references_json", "TEXT"),
        ]

        for col_name, col_type in new_columns:
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE documents ADD COLUMN {col_name} {col_type}")
                    logger.info(f"Added column {col_name} to documents table")
                except sqlite3.OperationalError:
                    pass  # Column already exists

    def register(self, metadata: DocumentMetadata) -> str:
        """
        Register a document in the registry.

        Args:
            metadata: DocumentMetadata object

        Returns:
            doc_id of registered document
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Serialize type-specific metadata
            type_metadata = None
            if metadata.paper_metadata:
                type_metadata = metadata.paper_metadata.model_dump_json()
            elif metadata.grant_metadata:
                type_metadata = metadata.grant_metadata.model_dump_json()
            elif metadata.meeting_metadata:
                type_metadata = metadata.meeting_metadata.model_dump_json()
            elif metadata.spreadsheet_metadata:
                type_metadata = metadata.spreadsheet_metadata.model_dump_json()
            elif metadata.code_metadata:
                type_metadata = metadata.code_metadata.model_dump_json()

            # Serialize VLM-extracted content
            figures_json = json.dumps([f.model_dump() for f in metadata.figures]) if metadata.figures else None
            tables_json = json.dumps([t.model_dump() for t in metadata.tables]) if metadata.tables else None
            references_json = json.dumps([r.model_dump() for r in metadata.references]) if metadata.references else None

            # Get extraction confidence
            extraction_confidence = None
            if metadata.extraction_confidence:
                extraction_confidence = metadata.extraction_confidence.overall

            # Check if document already exists (by file_path)
            cursor.execute(
                'SELECT doc_id FROM documents WHERE file_path = ? AND user_id = ?',
                (metadata.file_path, metadata.user_id)
            )
            existing = cursor.fetchone()

            if existing:
                # Update existing document
                cursor.execute('''
                    UPDATE documents SET
                        file_name = ?, file_hash = ?, doc_type = ?, title = ?,
                        date = ?, page_count = ?, has_abstract = ?, has_tables = ?,
                        has_figures = ?, searchable_text = ?, collection_name = ?,
                        type_metadata = ?, updated_at = ?,
                        vlm_model = ?, extraction_confidence = ?,
                        figure_count = ?, table_count = ?, reference_count = ?,
                        figures_json = ?, tables_json = ?, references_json = ?
                    WHERE doc_id = ?
                ''', (
                    metadata.file_name, metadata.file_hash, metadata.doc_type.value,
                    metadata.title, metadata.date, metadata.page_count,
                    int(metadata.has_abstract), int(metadata.has_tables),
                    int(metadata.has_figures), metadata.searchable_text,
                    metadata.collection_name, type_metadata,
                    metadata.updated_at.isoformat(),
                    metadata.vlm_model, extraction_confidence,
                    len(metadata.figures), len(metadata.tables), len(metadata.references),
                    figures_json, tables_json, references_json,
                    existing['doc_id']
                ))
                metadata.doc_id = existing['doc_id']
            else:
                # Insert new document
                cursor.execute('''
                    INSERT INTO documents (
                        doc_id, file_path, file_name, file_hash, doc_type, title,
                        date, page_count, has_abstract, has_tables, has_figures,
                        searchable_text, collection_name, user_id, type_metadata,
                        created_at, updated_at,
                        vlm_model, extraction_confidence,
                        figure_count, table_count, reference_count,
                        figures_json, tables_json, references_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metadata.doc_id, metadata.file_path, metadata.file_name,
                    metadata.file_hash, metadata.doc_type.value, metadata.title,
                    metadata.date, metadata.page_count, int(metadata.has_abstract),
                    int(metadata.has_tables), int(metadata.has_figures),
                    metadata.searchable_text, metadata.collection_name,
                    metadata.user_id, type_metadata,
                    metadata.created_at.isoformat(), metadata.updated_at.isoformat(),
                    metadata.vlm_model, extraction_confidence,
                    len(metadata.figures), len(metadata.tables), len(metadata.references),
                    figures_json, tables_json, references_json
                ))

            # Clear old authors and insert new
            cursor.execute('DELETE FROM document_authors WHERE doc_id = ?', (metadata.doc_id,))
            for author in metadata.authors:
                cursor.execute(
                    'INSERT INTO document_authors (doc_id, author_name, is_variant) VALUES (?, ?, 0)',
                    (metadata.doc_id, author)
                )
            # Add generated variants
            for variant in metadata.get_author_search_variants():
                if variant not in metadata.authors:
                    cursor.execute(
                        'INSERT INTO document_authors (doc_id, author_name, is_variant) VALUES (?, ?, 1)',
                        (metadata.doc_id, variant)
                    )

            # Clear old sections and insert new
            cursor.execute('DELETE FROM document_sections WHERE doc_id = ?', (metadata.doc_id,))
            for i, section in enumerate(metadata.sections):
                cursor.execute(
                    'INSERT INTO document_sections (doc_id, section_name, section_order) VALUES (?, ?, ?)',
                    (metadata.doc_id, section, i)
                )

        logger.info(f"Registered document: {metadata.file_name} ({metadata.doc_type.value}) - {len(metadata.authors)} authors")
        return metadata.doc_id

    def get_by_author(
        self,
        author_query: str,
        collection_name: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find all documents by author name (fuzzy match).

        Args:
            author_query: Author name to search (matches variants too)
            collection_name: Optional filter by collection
            user_id: Optional filter by user

        Returns:
            List of matching document metadata dicts
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Use LIKE for fuzzy matching (case-insensitive via COLLATE NOCASE index)
            query = '''
                SELECT DISTINCT d.*
                FROM documents d
                JOIN document_authors a ON d.doc_id = a.doc_id
                WHERE a.author_name LIKE ?
            '''
            params = [f'%{author_query}%']

            if collection_name:
                query += ' AND d.collection_name = ?'
                params.append(collection_name)
            if user_id:
                query += ' AND d.user_id = ?'
                params.append(user_id)

            query += ' ORDER BY d.created_at DESC'

            cursor.execute(query, params)
            results = []
            for row in cursor.fetchall():
                doc = dict(row)
                # Get authors for this document
                cursor.execute(
                    'SELECT author_name FROM document_authors WHERE doc_id = ? AND is_variant = 0',
                    (doc['doc_id'],)
                )
                doc['authors'] = [r['author_name'] for r in cursor.fetchall()]
                results.append(doc)

            return results

    def get_by_type(
        self,
        doc_type: DocumentType,
        collection_name: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find all documents of a specific type."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = 'SELECT * FROM documents WHERE doc_type = ?'
            params = [doc_type.value]

            if collection_name:
                query += ' AND collection_name = ?'
                params.append(collection_name)
            if user_id:
                query += ' AND user_id = ?'
                params.append(user_id)

            query += ' ORDER BY created_at DESC'

            cursor.execute(query, params)
            results = []
            for row in cursor.fetchall():
                doc = dict(row)
                cursor.execute(
                    'SELECT author_name FROM document_authors WHERE doc_id = ? AND is_variant = 0',
                    (doc['doc_id'],)
                )
                doc['authors'] = [r['author_name'] for r in cursor.fetchall()]
                results.append(doc)

            return results

    def search_title(
        self,
        title_query: str,
        collection_name: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Full-text search on document titles."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Use FTS for fast title search
            query = '''
                SELECT d.* FROM documents d
                WHERE d.doc_id IN (
                    SELECT doc_id FROM documents_fts WHERE title MATCH ?
                )
            '''
            params = [f'"{title_query}"']  # Quote for phrase match

            if collection_name:
                query += ' AND d.collection_name = ?'
                params.append(collection_name)
            if user_id:
                query += ' AND d.user_id = ?'
                params.append(user_id)

            cursor.execute(query, params)
            results = []
            for row in cursor.fetchall():
                doc = dict(row)
                cursor.execute(
                    'SELECT author_name FROM document_authors WHERE doc_id = ? AND is_variant = 0',
                    (doc['doc_id'],)
                )
                doc['authors'] = [r['author_name'] for r in cursor.fetchall()]
                results.append(doc)

            return results

    def search_fulltext(
        self,
        query: str,
        collection_name: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Full-text search on title and searchable_text."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            sql = '''
                SELECT d.* FROM documents d
                WHERE d.doc_id IN (
                    SELECT doc_id FROM documents_fts WHERE documents_fts MATCH ?
                )
            '''
            params = [query]

            if collection_name:
                sql += ' AND d.collection_name = ?'
                params.append(collection_name)
            if user_id:
                sql += ' AND d.user_id = ?'
                params.append(user_id)

            cursor.execute(sql, params)
            results = []
            for row in cursor.fetchall():
                doc = dict(row)
                cursor.execute(
                    'SELECT author_name FROM document_authors WHERE doc_id = ? AND is_variant = 0',
                    (doc['doc_id'],)
                )
                doc['authors'] = [r['author_name'] for r in cursor.fetchall()]
                results.append(doc)

            return results

    def get_doc_ids_by_author(
        self,
        author_query: str,
        collection_name: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[str]:
        """Get just the doc_ids for an author (for filtering vector search)."""
        docs = self.get_by_author(author_query, collection_name, user_id)
        return [d['doc_id'] for d in docs]

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a single document by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM documents WHERE doc_id = ?', (doc_id,))
            row = cursor.fetchone()

            if not row:
                return None

            doc = dict(row)
            cursor.execute(
                'SELECT author_name FROM document_authors WHERE doc_id = ? AND is_variant = 0',
                (doc_id,)
            )
            doc['authors'] = [r['author_name'] for r in cursor.fetchall()]

            cursor.execute(
                'SELECT section_name FROM document_sections WHERE doc_id = ? ORDER BY section_order',
                (doc_id,)
            )
            doc['sections'] = [r['section_name'] for r in cursor.fetchall()]

            # Deserialize VLM-extracted content
            doc['figures'] = json.loads(doc['figures_json']) if doc.get('figures_json') else []
            doc['tables'] = json.loads(doc['tables_json']) if doc.get('tables_json') else []
            doc['references'] = json.loads(doc['references_json']) if doc.get('references_json') else []

            return doc

    def get_all_documents(
        self,
        collection_name: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all documents (paginated)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = 'SELECT * FROM documents WHERE 1=1'
            params = []

            if collection_name:
                query += ' AND collection_name = ?'
                params.append(collection_name)
            if user_id:
                query += ' AND user_id = ?'
                params.append(user_id)

            query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])

            cursor.execute(query, params)
            results = []
            for row in cursor.fetchall():
                doc = dict(row)
                cursor.execute(
                    'SELECT author_name FROM document_authors WHERE doc_id = ? AND is_variant = 0',
                    (doc['doc_id'],)
                )
                doc['authors'] = [r['author_name'] for r in cursor.fetchall()]
                results.append(doc)

            return results

    def get_stats(
        self,
        collection_name: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get statistics about the registry."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            where_clause = "WHERE 1=1"
            params = []
            if collection_name:
                where_clause += " AND collection_name = ?"
                params.append(collection_name)
            if user_id:
                where_clause += " AND user_id = ?"
                params.append(user_id)

            # Total documents
            cursor.execute(f'SELECT COUNT(*) FROM documents {where_clause}', params)
            total = cursor.fetchone()[0]

            # By type
            cursor.execute(
                f'SELECT doc_type, COUNT(*) as count FROM documents {where_clause} GROUP BY doc_type',
                params
            )
            by_type = {row['doc_type']: row['count'] for row in cursor.fetchall()}

            # Unique authors
            cursor.execute(
                f'''SELECT COUNT(DISTINCT a.author_name) FROM document_authors a
                    JOIN documents d ON a.doc_id = d.doc_id
                    {where_clause} AND a.is_variant = 0''',
                params
            )
            unique_authors = cursor.fetchone()[0]

            # VLM extraction stats
            cursor.execute(
                f'''SELECT
                    SUM(COALESCE(figure_count, 0)) as total_figures,
                    SUM(COALESCE(table_count, 0)) as total_tables,
                    SUM(COALESCE(reference_count, 0)) as total_references,
                    AVG(extraction_confidence) as avg_confidence,
                    COUNT(CASE WHEN vlm_model IS NOT NULL THEN 1 END) as vlm_analyzed_count
                FROM documents {where_clause}''',
                params
            )
            vlm_row = cursor.fetchone()

            # VLM models used
            cursor.execute(
                f'''SELECT vlm_model, COUNT(*) as count FROM documents
                    {where_clause} AND vlm_model IS NOT NULL
                    GROUP BY vlm_model''',
                params
            )
            vlm_models = {row['vlm_model']: row['count'] for row in cursor.fetchall()}

            return {
                "total_documents": total,
                "by_type": by_type,
                "unique_authors": unique_authors,
                "total_figures": vlm_row['total_figures'] or 0,
                "total_tables": vlm_row['total_tables'] or 0,
                "total_references": vlm_row['total_references'] or 0,
                "avg_extraction_confidence": round(vlm_row['avg_confidence'] or 0, 3),
                "vlm_analyzed_count": vlm_row['vlm_analyzed_count'] or 0,
                "vlm_models": vlm_models
            }

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the registry."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Cascading delete handles authors and sections
            cursor.execute('DELETE FROM documents WHERE doc_id = ?', (doc_id,))
            deleted = cursor.rowcount > 0

            if deleted:
                logger.info(f"Deleted document: {doc_id}")

            return deleted

    def delete_by_file_path(self, file_path: str, user_id: Optional[str] = None) -> bool:
        """Delete document by file path."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if user_id:
                cursor.execute(
                    'DELETE FROM documents WHERE file_path = ? AND user_id = ?',
                    (file_path, user_id)
                )
            else:
                cursor.execute('DELETE FROM documents WHERE file_path = ?', (file_path,))

            return cursor.rowcount > 0
