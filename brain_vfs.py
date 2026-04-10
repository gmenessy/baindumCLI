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
        # Assume schema.sql has run, but ensure tables exist for testing
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
            conn.execute('''
                CREATE TABLE IF NOT EXISTS vfs_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    namespace TEXT NOT NULL,
                    snapshot_data TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    def list_namespace(self, namespace: str) -> List[VFSNode]:
        """Lists all nodes under a given namespace (e.g., vfs://dumps)."""
        nodes = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT path, layer, content, metadata, updated_at FROM vfs_nodes WHERE path LIKE ?", (f"{namespace}%",))
            for row in cursor.fetchall():
                path, layer, content_str, meta_str, updated_at_str = row
                try:
                    content = json.loads(content_str)
                except json.JSONDecodeError:
                    content = content_str
                nodes.append(VFSNode(
                    path=path,
                    layer=layer,
                    content=content,
                    metadata=json.loads(meta_str),
                    updated_at=datetime.fromisoformat(updated_at_str) if updated_at_str else datetime.now(timezone.utc)
                ))
        return nodes

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
        import uuid
        snapshot_id = f"snap-{uuid.uuid4().hex[:8]}"

        nodes = self.list_namespace(namespace)
        snapshot_data = []
        for n in nodes:
            snapshot_data.append({
                "path": n.path,
                "layer": n.layer,
                "content": n.content,
                "metadata": n.metadata,
                "updated_at": n.updated_at.isoformat()
            })

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO vfs_snapshots (snapshot_id, namespace, snapshot_data) VALUES (?, ?, ?)",
                (snapshot_id, namespace, json.dumps(snapshot_data))
            )
        return snapshot_id

    def restore(self, snapshot_id: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT namespace, snapshot_data FROM vfs_snapshots WHERE snapshot_id = ?", (snapshot_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Snapshot {snapshot_id} not found.")

            namespace, data_str = row
            snapshot_data = json.loads(data_str)

            # 1. Clear current namespace
            conn.execute("DELETE FROM vfs_nodes WHERE path LIKE ?", (f"{namespace}%",))

            # 2. Restore data
            for n in snapshot_data:
                content_str = json.dumps(n["content"]) if isinstance(n["content"], (dict, list)) else str(n["content"])
                meta_str = json.dumps(n["metadata"])
                conn.execute('''
                    INSERT INTO vfs_nodes (path, layer, content, metadata, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (n["path"], n["layer"], content_str, meta_str, n["updated_at"]))


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

    def list_namespace(self, namespace: str) -> List[VFSNode]:
        if hasattr(self.storage, 'list_namespace'):
            return self.storage.list_namespace(namespace)
        return []

    def snapshot(self, namespace: str) -> str:
        return self.storage.snapshot(namespace)

    def restore(self, snapshot_id: str):
        if hasattr(self.storage, 'restore'):
            self.storage.restore(snapshot_id)

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
