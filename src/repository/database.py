# database.py
import sqlite3
import threading
from contextlib import contextmanager
from models.secure_data import SecureData
from models.secure_message import SecureMessage
from models.secure_capsule import SecureCapsule
from models.note_group import NoteGroup


class Database:
    """Operaciones SQLite. Con bóveda abierta reutiliza la conexión :memory: del Vault."""

    def __init__(self, db_name="app.db", on_write=None, conn=None, lock=None):
        self.db_name = db_name
        self.on_write = on_write
        self._conn = conn  # conexión anclada (no cerrar)
        self._lock = lock if lock is not None else threading.RLock()
        self.init_db()

    def init_db(self):
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS data (
                    id INTEGER PRIMARY KEY,
                    hash TEXT NOT NULL,
                    key TEXT NOT NULL,
                    extension TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    content_encrypted TEXT NOT NULL,
                    folder TEXT NOT NULL DEFAULT ''
                )
                """
            )
            # migración bóvedas antiguas sin columna folder
            cols = {r[1] for r in cursor.execute("PRAGMA table_info(messages)")}
            if "folder" not in cols:
                cursor.execute(
                    "ALTER TABLE messages ADD COLUMN folder TEXT NOT NULL DEFAULT ''"
                )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS capsules (
                    id INTEGER PRIMARY KEY,
                    label TEXT NOT NULL,
                    bros_path TEXT NOT NULL,
                    key TEXT NOT NULL,
                    unlock_at TEXT NOT NULL,
                    extension TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS note_groups (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    description TEXT NOT NULL DEFAULT ''
                )
                """
            )
            # Migrar nombres de carpeta ya usados en notas → grupos sin descripción
            cursor.execute("SELECT DISTINCT folder FROM messages WHERE folder != ''")
            for (folder,) in cursor.fetchall():
                if not folder:
                    continue
                cursor.execute(
                    "INSERT OR IGNORE INTO note_groups (title, description) VALUES (?, '')",
                    (folder,),
                )
            self._commit(conn)

    def _commit(self, conn, *, persist=True):
        conn.commit()
        if persist and self.on_write:
            self.on_write()

    @contextmanager
    def getConnection(self):
        with self._lock:
            if self._conn is not None:
                yield self._conn
                return
            conn = sqlite3.connect(self.db_name, check_same_thread=False)
            try:
                yield conn
            finally:
                conn.close()

    def addItem(self, hash, key, extension):
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO data (hash, key, extension) VALUES (?, ?, ?)",
                (hash, key, extension),
            )
            self._commit(conn)
            return cursor.lastrowid

    def getItemByHash(self, hash):
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM data WHERE hash = ?", (hash,))
            row = cursor.fetchone()
            return SecureData.from_db(row) if row else None

    def deleteItemById(self, item_id):
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM data WHERE id = ?", (item_id,))
            self._commit(conn)
            return cursor.rowcount

    def updateItemKey(self, item_id, new_key):
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE data SET key = ? WHERE id = ?", (new_key, item_id)
            )
            self._commit(conn)
            return cursor.rowcount

    def getAllItems(self):
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM data")
            return [SecureData.from_db(row) for row in cursor.fetchall()]

    def addMessage(self, title, content_encrypted, folder=""):
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (title, content_encrypted, folder) VALUES (?, ?, ?)",
                (title, content_encrypted, folder or ""),
            )
            self._commit(conn)
            return cursor.lastrowid

    def getAllMessages(self):
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, title, content_encrypted, folder FROM messages "
                "ORDER BY folder COLLATE NOCASE, title COLLATE NOCASE"
            )
            return [SecureMessage.from_db(row) for row in cursor.fetchall()]

    def getMessageById(self, msg_id):
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, title, content_encrypted, folder FROM messages WHERE id = ?",
                (msg_id,),
            )
            row = cursor.fetchone()
            return SecureMessage.from_db(row) if row else None

    def updateMessage(self, msg_id, title, content_encrypted, folder=None):
        with self.getConnection() as conn:
            cursor = conn.cursor()
            if folder is None:
                cursor.execute(
                    "UPDATE messages SET title = ?, content_encrypted = ? WHERE id = ?",
                    (title, content_encrypted, msg_id),
                )
            else:
                cursor.execute(
                    "UPDATE messages SET title = ?, content_encrypted = ?, folder = ? WHERE id = ?",
                    (title, content_encrypted, folder or "", msg_id),
                )
            self._commit(conn)
            return cursor.rowcount

    def getMessageFolders(self):
        """Títulos de grupo: tabla note_groups + carpetas huérfanas en notes."""
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT title FROM note_groups ORDER BY title COLLATE NOCASE"
            )
            names = {r[0] for r in cursor.fetchall() if r[0]}
            cursor.execute(
                "SELECT DISTINCT folder FROM messages WHERE folder != ''"
            )
            names.update(r[0] for r in cursor.fetchall() if r[0])
            return sorted(names, key=str.lower)

    def addNoteGroup(self, title, description=""):
        title = (title or "").strip()
        if not title:
            raise ValueError("El grupo necesita un título")
        with self.getConnection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO note_groups (title, description) VALUES (?, ?)",
                    (title, description or ""),
                )
            except sqlite3.IntegrityError:
                raise ValueError(f"Ya existe un grupo «{title}»") from None
            self._commit(conn)
            return cursor.lastrowid

    def upsertNoteGroup(self, title, description=None):
        """Crea el grupo si no existe. Si description es None y ya existe, no toca desc."""
        title = (title or "").strip()
        if not title:
            raise ValueError("El grupo necesita un título")
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, description FROM note_groups WHERE title = ? COLLATE NOCASE",
                (title,),
            )
            row = cursor.fetchone()
            if row:
                if description is not None:
                    cursor.execute(
                        "UPDATE note_groups SET description = ? WHERE id = ?",
                        (description, row[0]),
                    )
                    self._commit(conn)
                return row[0]
            cursor.execute(
                "INSERT INTO note_groups (title, description) VALUES (?, ?)",
                (title, description or ""),
            )
            self._commit(conn)
            return cursor.lastrowid

    def updateNoteGroup(self, group_id, title, description):
        title = (title or "").strip()
        if not title:
            raise ValueError("El grupo necesita un título")
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT title FROM note_groups WHERE id = ?", (group_id,)
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError("Grupo no encontrado")
            old_title = row[0]
            cursor.execute(
                "UPDATE note_groups SET title = ?, description = ? WHERE id = ?",
                (title, description or "", group_id),
            )
            if old_title != title:
                cursor.execute(
                    "UPDATE messages SET folder = ? WHERE folder = ?",
                    (title, old_title),
                )
            self._commit(conn)
            return cursor.rowcount

    def getNoteGroupByTitle(self, title):
        title = (title or "").strip()
        if not title:
            return None
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, title, description FROM note_groups WHERE title = ? COLLATE NOCASE",
                (title,),
            )
            row = cursor.fetchone()
            return NoteGroup.from_db(row) if row else None

    def getAllNoteGroups(self):
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, title, description FROM note_groups ORDER BY title COLLATE NOCASE"
            )
            return [NoteGroup.from_db(r) for r in cursor.fetchall()]

    def deleteNoteGroup(self, title, *, move_notes_to_root=True):
        title = (title or "").strip()
        if not title:
            return 0
        with self.getConnection() as conn:
            cursor = conn.cursor()
            if move_notes_to_root:
                cursor.execute(
                    "UPDATE messages SET folder = '' WHERE folder = ? COLLATE NOCASE",
                    (title,),
                )
            cursor.execute(
                "DELETE FROM note_groups WHERE title = ? COLLATE NOCASE", (title,)
            )
            self._commit(conn)
            return cursor.rowcount

    def deleteMessage(self, msg_id):
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
            self._commit(conn)
            return cursor.rowcount

    def addCapsule(self, label, bros_path, key, unlock_at, extension):
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO capsules (label, bros_path, key, unlock_at, extension)
                VALUES (?, ?, ?, ?, ?)
                """,
                (label, bros_path, key, unlock_at, extension),
            )
            self._commit(conn)
            return cursor.lastrowid

    def getAllCapsules(self):
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM capsules ORDER BY unlock_at")
            return [SecureCapsule.from_db(row) for row in cursor.fetchall()]

    def getCapsuleById(self, capsule_id):
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM capsules WHERE id = ?", (capsule_id,))
            row = cursor.fetchone()
            return SecureCapsule.from_db(row) if row else None

    def deleteCapsule(self, capsule_id):
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM capsules WHERE id = ?", (capsule_id,))
            self._commit(conn)
            return cursor.rowcount
