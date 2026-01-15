#import sqlite3
#con = sqlite3.connect('secure.db')
#cur = con.cursor()
# database.py
import sqlite3
from contextlib import contextmanager
from models.secure_data import SecureData
from models.secure_message import SecureMessage

class Database:
    """Clase para manejar las operaciones SQLite de almacenamiento de claves."""
    def __init__(self, db_name='app.db'):
        """Inicializa la base de datos."""
        self.db_name = db_name
        self.init_db()
    
    def init_db(self):
        """Inicializar base de datos con tablas si no existen."""
        with self.getConnection() as conn:
            cursor = conn.cursor()
            # Crear tablas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data (
                    id INTEGER PRIMARY KEY,
                    hash TEXT NOT NULL,
                    key TEXT NOT NULL,
                    extension TEXT NOT NULL
                )
            ''')
            # Crear tabla de mensajes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    content_encrypted TEXT NOT NULL
                )
            ''')
            conn.commit()
    
    @contextmanager
    def getConnection(self):
        """Manejador de contexto para asegurar el cierre de conexiones SQLite."""
        conn = sqlite3.connect(self.db_name)
        try:
            yield conn
        finally:
            conn.close()
    
    # Métodos específicos de la aplicación
    def addItem(self, hash, key, extension):
        """Inserta un nuevo registro seguro en la base de datos."""
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO data (hash, key, extension) VALUES (?, ?, ?)",
                (hash, key, extension)
            )
            conn.commit()
            return cursor.lastrowid

    def getItemByHash(self, hash):
        """Busca y retorna un registro por su hash."""
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM data WHERE hash = ?",
                (hash,)
            )
            row = cursor.fetchone()
            if row:
                return SecureData.from_db(row)
            return None

    def deleteItemById(self, item_id):
        """Elimina un registro de la base de datos."""
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM data WHERE id = ?",
                (item_id,)
            )
            conn.commit()
            return cursor.rowcount

    def updateItemKey(self, item_id, new_key):
        """Actualiza la clave de un registro existente."""
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE data SET key = ? WHERE id = ?",
                (new_key, item_id)
            )
            conn.commit()
            return cursor.rowcount

    def getAllItems(self):
        """Obtiene una lista de todos los registros en la base de datos."""
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM data")
            rows = cursor.fetchall()
            return [SecureData.from_db(row) for row in rows]

    # Métodos para mensajes
    def addMessage(self, title, content_encrypted):
        """Inserta un nuevo mensaje cifrado."""
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (title, content_encrypted) VALUES (?, ?)",
                (title, content_encrypted)
            )
            conn.commit()
            return cursor.lastrowid

    def getAllMessages(self):
        """Obtiene todos los mensajes."""
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM messages")
            rows = cursor.fetchall()
            return [SecureMessage.from_db(row) for row in rows]
            
    def getMessageById(self, msg_id):
        """Obtiene un mensaje por ID."""
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM messages WHERE id = ?", (msg_id,))
            row = cursor.fetchone()
            if row:
                return SecureMessage.from_db(row)
            return None

    def deleteMessage(self, msg_id):
        """Elimina un mensaje por ID."""
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
            conn.commit()
            return cursor.rowcount

        