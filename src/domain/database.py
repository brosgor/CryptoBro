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
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Crear tablas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    precio REAL,
                    stock INTEGER DEFAULT 0
                )
            ''')
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Manejador de contexto para conexiones"""
        conn = sqlite3.connect(self.db_name)
        try:
            yield conn
        finally:
            conn.close()
    
    # Métodos específicos de la aplicación
    def agregar_producto(self, nombre, precio, stock=0):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO productos (nombre, precio, stock) VALUES (?, ?, ?)",
                (nombre, precio, stock)
            )
            conn.commit()
            return cursor.lastrowid

