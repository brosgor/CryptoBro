#import sqlite3
#con = sqlite3.connect('secure.db')
#cur = con.cursor()
# database.py
import sqlite3
from contextlib import contextmanager

class Database:
    def __init__(self, db_name='app.db'):
        self.db_name = db_name
        self.init_db()
    
    def init_db(self):
        """Inicializar base de datos con tablas"""
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
            conn.commit()
    
    @contextmanager
    def getConnection(self):
        """Manejador de contexto para conexiones"""
        conn = sqlite3.connect(self.db_name)
        try:
            yield conn
        finally:
            conn.close()
    
    # Métodos específicos de la aplicación
    def addItem(self, hash, key, extension):
        with self.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO data (hash, key, extension) VALUES (?, ?, ?)",
                (hash, key, extension)
            )
            conn.commit()
            return cursor.lastrowid

