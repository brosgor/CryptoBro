"""
Entry point: unlock vault → GUI → lock vault on exit.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tkinter as tk
from domain.vault import Vault
from gui.unlock import UnlockDialog
from gui.app import CryptoApp


# Allow `python src/main.py` from repo root — if restore closed unlock without ok, reopen once
def main():
    vault = Vault()

    while True:
        unlock_root = tk.Tk()
        dialog = UnlockDialog(unlock_root, vault)
        unlock_root.mainloop()
        if dialog.ok:
            break
        if dialog.retry:
            continue
        return

    root = tk.Tk()
    app = CryptoApp(root, vault)

    def on_close():
        try:
            app.service.lock()
        except Exception:
            vault.lock()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    def _autosave():
        try:
            vault.flush()
        except Exception:
            pass
        root.after(60_000, _autosave)

    root.after(60_000, _autosave)
    root.mainloop()
    try:
        vault.lock()
    except Exception:
        pass


if __name__ == "__main__":
    main()
