# database.py
import sqlite3
import threading
from contextlib import contextmanager
from models.secure_data import SecureData
from models.secure_message import SecureMessage
from models.secure_capsule import SecureCapsule


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
                    content_encrypted TEXT NOT NULL
                )
                """
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

    def addMessage(self, title, content_encrypted):
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (title, content_encrypted) VALUES (?, ?)",
                (title, content_encrypted),
            )
            self._commit(conn)
            return cursor.lastrowid

    def getAllMessages(self):
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM messages")
            return [SecureMessage.from_db(row) for row in cursor.fetchall()]

    def getMessageById(self, msg_id):
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM messages WHERE id = ?", (msg_id,))
            row = cursor.fetchone()
            return SecureMessage.from_db(row) if row else None

    def updateMessage(self, msg_id, title, content_encrypted):
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE messages SET title = ?, content_encrypted = ? WHERE id = ?",
                (title, content_encrypted, msg_id),
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
