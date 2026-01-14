from gui.app import CryptoApp
import tkinter as tk

def main():
    root = tk.Tk()
    app = CryptoApp(root) # noqa: F841
    root.mainloop()

if __name__== "__main__":
    main()