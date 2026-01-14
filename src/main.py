"""
Módulo de entrada principal para CryptoBro.

Este script inicializa la ventana principal de Tkinter y lanza la aplicación
CryptoApp.
"""
from gui.app import CryptoApp
import tkinter as tk

def main():
    """Inicializa y ejecuta el bucle principal de la aplicación."""
    root = tk.Tk()
    app = CryptoApp(root) # noqa: F841
    root.mainloop()

if __name__== "__main__":
    main()