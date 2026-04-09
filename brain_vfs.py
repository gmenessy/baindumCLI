from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import sqlite3
import json

@dataclass
class VFSNode:
    path: str
    layer: str
    content: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SQLiteBackend:
    """A minimal SQLite backend adapter for VFS."""
    def __init__(self, db_path: str = "metadata.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        # Assume schema.sql has run, but ensure table exists for testing
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS vfs_nodes (
                    path TEXT PRIMARY KEY,
                    layer TEXT,
                    content TEXT,
                    metadata TEXT,
                    updated_at DATETIME
                )
            ''')

    def read(self, path: str) -> Optional[VFSNode]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT layer, content, metadata, updated_at FROM vfs_nodes WHERE path = ?", (path,))
            row = cursor.fetchone()
            if row:
                layer, content_str, meta_str, updated_at_str = row
                try:
                    content = json.loads(content_str)
                except json.JSONDecodeError:
                    content = content_str

                return VFSNode(
                    path=path,
                    layer=layer,
                    content=content,
                    metadata=json.loads(meta_str),
                    updated_at=datetime.fromisoformat(updated_at_str) if updated_at_str else datetime.now(timezone.utc)
                )
        return None

    def write(self, node: VFSNode):
        with sqlite3.connect(self.db_path) as conn:
            content_str = json.dumps(node.content) if isinstance(node.content, (dict, list)) else str(node.content)
            meta_str = json.dumps(node.metadata)
            conn.execute('''
                INSERT INTO vfs_nodes (path, layer, content, metadata, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    layer=excluded.layer,
                    content=excluded.content,
                    metadata=excluded.metadata,
                    updated_at=excluded.updated_at
            ''', (node.path, node.layer, content_str, meta_str, node.updated_at.isoformat()))

    def delete(self, path: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM vfs_nodes WHERE path = ?", (path,))

    def snapshot(self, namespace: str) -> str:
        # Simplistic mock for snapshotting
        import uuid
        return f"snap-{uuid.uuid4().hex[:8]}"


class BrainVFS:
    """The central runtime abstraction for all memory operations."""
    def __init__(self, storage_backend, vector_backend=None):
        self.storage = storage_backend
        self.vector = vector_backend
        self.mounts = {}

    def mount(self, namespace: str, backend: str):
        self.mounts[namespace] = backend

    def read(self, path: str) -> Optional[VFSNode]:
        return self.storage.read(path)

    def write(self, node: VFSNode):
        self.storage.write(node)
        if self.vector:
            # Note: vector_backend must implement `index(path, string)`
            self.vector.index(node.path, str(node.content))

    def delete(self, path: str):
        self.storage.delete(path)

    def snapshot(self, namespace: str) -> str:
        return self.storage.snapshot(namespace)

    def promote(self, source_path: str, target_path: str):
        """Promotes a VFS node from one path to another (e.g. Dump -> Wiki)."""
        node = self.read(source_path)
        if node:
            # Extract layer from target path (e.g., vfs://wiki/projects/... -> wiki)
            parts = target_path.split('/')
            layer = parts[2] if len(parts) > 2 else "unknown"

            promoted = VFSNode(
                path=target_path,
                layer=layer,
                content=node.content,
                metadata=node.metadata.copy(),
            )
            self.write(promoted)
