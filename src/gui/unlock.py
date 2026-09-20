"""Pantalla: elegir bóveda / registrar / desbloquear / eliminar / restaurar."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from gui.widgets import RoundedButton
from gui import theme as T
from gui.theme import apply_ttk_theme

from domain.vault import Vault, VaultError
from domain.paths import list_vault_names, sanitize_vault_name


class UnlockDialog:
    def __init__(self, root: tk.Tk, vault: Vault):
        self.root = root
        self.vault = vault
        self.ok = False
        self.retry = False

        root.title("CryptoBro — Bóvedas")
        root.geometry("480x520")
        root.configure(background=T.BG)
        root.resizable(False, False)

        style = ttk.Style()
        apply_ttk_theme(root, style)

        frame = ttk.Frame(root, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="CryptoBro", font=T.FONT_TITLE).pack(pady=(0, 4))
        ttk.Label(
            frame,
            text="Puedes tener varias bóvedas. Cada una con su propia clave.",
            style="Hint.TLabel",
        ).pack(pady=(0, 12))

        ttk.Label(frame, text="Bóveda").pack(anchor="w")
        row = ttk.Frame(frame)
        row.pack(fill="x", pady=4)
        self.vault_var = tk.StringVar()
        self.combo = ttk.Combobox(row, textvariable=self.vault_var, state="readonly")
        self.combo.pack(side="left", fill="x", expand=True)
        self.combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_mode())

        self.pw = tk.StringVar()
        self.pw2 = tk.StringVar()
        self.name_new = tk.StringVar()

        self.form = ttk.Frame(frame)
        self.form.pack(fill="both", expand=True, pady=10)

        self.actions = ttk.Frame(frame)
        self.actions.pack(fill="x", pady=6)

        RoundedButton(self.actions, text="Nueva bóveda", command=self._show_create).pack(
            fill="x", pady=3
        )
        RoundedButton(
            self.actions, text="Eliminar bóveda seleccionada", command=self._delete_selected
        ).pack(fill="x", pady=3)
        RoundedButton(
            self.actions, text="Restaurar backup (.gor)", command=self._restore
        ).pack(fill="x", pady=3)

        self._reload_list()
        self._refresh_mode()

    def _clear_form(self):
        for w in self.form.winfo_children():
            w.destroy()

    def _reload_list(self):
        names = list_vault_names()
        self.combo["values"] = names
        if names:
            current = self.vault.name if self.vault.name in names else names[0]
            self.vault_var.set(current)
            self.vault.select(current)
        else:
            self.vault_var.set("")

    def _refresh_mode(self):
        self._clear_form()
        names = list_vault_names()
        selected = self.vault_var.get().strip()

        if not names:
            ttk.Label(
                self.form,
                text="Primera vez — crea tu primera bóveda",
                font=T.FONT_SUB,
            ).pack(anchor="w", pady=(0, 8))
            self._build_create_fields(default_name="personal")
            RoundedButton(
                self.form, text="Registrar clave de bloqueo", command=self._create
            ).pack(fill="x", pady=12)
            return

        if selected:
            try:
                self.vault.select(selected)
            except Exception:
                pass

        ttk.Label(
            self.form,
            text=f"Desbloquear «{selected}»",
            font=T.FONT_SUB,
        ).pack(anchor="w", pady=(0, 8))
        ttk.Label(self.form, text="Clave de bloqueo").pack(anchor="w")
        ent = ttk.Entry(self.form, textvariable=self.pw, show="*", width=40)
        ent.pack(fill="x", pady=2)
        ent.focus_set()
        ent.bind("<Return>", lambda e: self._unlock())
        RoundedButton(self.form, text="Desbloquear", command=self._unlock).pack(
            fill="x", pady=12
        )

    def _build_create_fields(self, default_name: str = ""):
        ttk.Label(self.form, text="Nombre de la bóveda").pack(anchor="w")
        self.name_new.set(default_name)
        ttk.Entry(self.form, textvariable=self.name_new).pack(fill="x", pady=2)
        ttk.Label(self.form, text="Clave de bloqueo (mín. 8)").pack(anchor="w", pady=(8, 0))
        ttk.Entry(self.form, textvariable=self.pw, show="*").pack(fill="x", pady=2)
        ttk.Label(self.form, text="Confirmar clave").pack(anchor="w", pady=(8, 0))
        ent2 = ttk.Entry(self.form, textvariable=self.pw2, show="*")
        ent2.pack(fill="x", pady=2)
        ent2.bind("<Return>", lambda e: self._create())

    def _show_create(self):
        self._clear_form()
        ttk.Label(self.form, text="Nueva bóveda", font=T.FONT_SUB).pack(
            anchor="w", pady=(0, 8)
        )
        self.pw.set("")
        self.pw2.set("")
        self._build_create_fields()
        RoundedButton(
            self.form, text="Registrar clave de bloqueo", command=self._create
        ).pack(fill="x", pady=12)
        RoundedButton(self.form, text="Volver", command=self._refresh_mode).pack(
            fill="x", pady=3
        )

    def _create(self):
        try:
            name = sanitize_vault_name(self.name_new.get())
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return
        a, b = self.pw.get(), self.pw2.get()
        if len(a) < 8:
            messagebox.showerror("Error", "La clave debe tener al menos 8 caracteres")
            return
        if a != b:
            messagebox.showerror("Error", "Las claves no coinciden")
            return
        try:
            self.vault.setup(a, name=name)
            self.ok = True
            self.root.destroy()
        except VaultError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _unlock(self):
        selected = self.vault_var.get().strip()
        if not selected:
            messagebox.showerror("Error", "Selecciona una bóveda")
            return
        if not self.pw.get():
            messagebox.showerror("Error", "Introduce tu clave de bloqueo")
            return
        try:
            self.vault.select(selected)
            self.vault.unlock(self.pw.get())
            self.ok = True
            self.root.destroy()
        except VaultError as e:
            messagebox.showerror("Error", str(e))

    def _delete_selected(self):
        selected = self.vault_var.get().strip()
        if not selected:
            messagebox.showerror("Error", "No hay bóveda seleccionada")
            return
        if not messagebox.askyesno(
            "Eliminar bóveda",
            f"¿Eliminar permanentemente la bóveda «{selected}»?\n"
            "Se borrarán notas, claves y cápsulas de ESA bóveda.\n"
            "Esta acción no se puede deshacer.",
        ):
            return
        pw = simpledialog.askstring(
            "Confirmar", f"Clave de bloqueo de «{selected}»:", show="*", parent=self.root
        )
        if not pw:
            return
        try:
            if not self.vault._locked and self.vault.name == selected:
                self.vault.lock()
            self.vault.delete_vault(selected, confirm_password=pw)
            messagebox.showinfo("Listo", f"Bóveda «{selected}» eliminada.")
            self.pw.set("")
            self._reload_list()
            self._refresh_mode()
        except VaultError as e:
            messagebox.showerror("Error", str(e))

    def _restore(self):
        path = filedialog.askopenfilename(
            title="Restaurar bóveda",
            filetypes=[
                ("Bóveda CryptoBro", "*.gor"),
                ("Backup legacy", "*.cbvault"),
                ("All", "*.*"),
            ],
        )
        if not path:
            return
        name = simpledialog.askstring(
            "Nombre",
            "¿Con qué nombre guardar esta bóveda restaurada?",
            initialvalue="restaurada",
            parent=self.root,
        )
        if not name:
            return
        try:
            sanitize_vault_name(name)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return
        overwrite = False
        try:
            from domain.paths import vault_gor_path

            if vault_gor_path(name).exists():
                if not messagebox.askyesno(
                    "Sobrescribir", f"«{name}» ya existe. ¿Sobrescribir?"
                ):
                    return
                overwrite = True
            self.vault.import_backup(path, vault_name=name, overwrite=overwrite)
            messagebox.showinfo(
                "Restaurado",
                f"Backup en «{name}». Selecciónala y desbloquea con su clave.",
            )
            self._reload_list()
            self.vault_var.set(sanitize_vault_name(name))
            self._refresh_mode()
        except VaultError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))
