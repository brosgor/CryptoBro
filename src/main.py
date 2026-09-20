"""
Entry point: unlock vault → GUI → lock vault on exit / cambiar bóveda.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tkinter as tk
from domain.vault import Vault
from gui.unlock import UnlockDialog
from gui.app import CryptoApp


def main():
    vault = Vault()

    while True:
        unlock_root = tk.Tk()
        dialog = UnlockDialog(unlock_root, vault)
        unlock_root.mainloop()
        if dialog.retry:
            continue
        if not dialog.ok:
            return

        root = tk.Tk()
        app = CryptoApp(root, vault)
        # app.switch_vault=True → volver al selector; False → salir del programa

        def on_close():
            try:
                app.service.lock()
            except Exception:
                vault.lock()
            app.want_switch_vault = False
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_close)

        def _autosave():
            try:
                vault.flush()
            except Exception:
                pass
            try:
                root.after(60_000, _autosave)
            except Exception:
                pass

        root.after(60_000, _autosave)
        root.mainloop()

        try:
            vault.lock()
        except Exception:
            pass

        if getattr(app, "want_switch_vault", False):
            continue
        return


if __name__ == "__main__":
    main()
