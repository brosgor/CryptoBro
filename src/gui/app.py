import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from service.cryptoService import CryptoService
from domain.vault import Vault
from domain.paths import ICON_PNG
from gui.widgets import RoundedButton, ScrollableFrame
from gui import theme as T
from gui.theme import apply_ttk_theme, page_header
import os

class CryptoApp:
    """Clase principal de la interfaz gráfica GUI basada en Tkinter."""
    def __init__(self, root, vault: Vault):
        """Inicializa la ventana principal, dimensiones y servicio."""
        self.root = root
        self.root.title("CryptoBro")
        self.root.geometry("900x600")
        self.root.minsize(720, 480)
        self.root.resizable(True, True)
        self._set_icon()
        try:
            self.root.iconname("CryptoBro")
        except tk.TclError:
            pass

        self.service = CryptoService(vault)
        self.want_switch_vault = False

        self.apply_theme()
        self.create_widgets()

    def _set_icon(self):
        try:
            if ICON_PNG.exists():
                img = tk.PhotoImage(file=str(ICON_PNG))
                self.root.iconphoto(True, img)
                self._icon_ref = img  # keep ref
        except tk.TclError:
            pass

    def apply_theme(self):
        """Tema claro unificado."""
        style = ttk.Style()
        apply_ttk_theme(self.root, style)

    def create_widgets(self):
        """Crea y organiza las pestañas principales de la aplicación."""
        tabControl = ttk.Notebook(self.root)
        self._notebook = tabControl

        self.tab_vault = ttk.Frame(tabControl)
        self.tab_encrypt = ttk.Frame(tabControl)
        self.tab_decrypt = ttk.Frame(tabControl)
        self.tab_capsules = ttk.Frame(tabControl)
        self.tab_messages = ttk.Frame(tabControl)
        self.tab_hash = ttk.Frame(tabControl)
        self.tab_gen = ttk.Frame(tabControl)
        self.tab_keys = ttk.Frame(tabControl)

        tabControl.add(self.tab_vault, text="Bóveda")
        tabControl.add(self.tab_encrypt, text="Cifrar")
        tabControl.add(self.tab_decrypt, text="Descifrar")
        tabControl.add(self.tab_capsules, text="Cápsulas")
        tabControl.add(self.tab_messages, text="Notas")
        tabControl.add(self.tab_hash, text="Hash")
        tabControl.add(self.tab_gen, text="Generador")
        tabControl.add(self.tab_keys, text="Claves")

        tabControl.pack(expand=1, fill="both", padx=10, pady=10)
        tabControl.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self.setup_vault_tab()
        self.setup_encrypt_tab()
        self.setup_decrypt_tab()
        self.setup_capsules_tab()
        self.setup_messages_tab()
        self.setup_hash_tab()
        self.setup_generator_tab()
        self.setup_keys_tab()

    def _on_tab_changed(self, _event=None):
        try:
            tab = self._notebook.nametowidget(self._notebook.select())
        except Exception:
            return
        if tab is getattr(self, "tab_messages", None):
            self.refresh_messages_list()
        elif tab is getattr(self, "tab_decrypt", None):
            self.refresh_bodega_list()
        elif tab is getattr(self, "tab_capsules", None) and hasattr(self, "refresh_capsules"):
            self.refresh_capsules()

    @staticmethod
    def _fmt_bytes(n: int) -> str:
        n = float(max(n, 0))
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if n < 1024 or unit == "TB":
                return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} TB"

    @staticmethod
    def _fmt_eta(seconds: float) -> str:
        if seconds < 0 or seconds != seconds:  # NaN
            return "…"
        s = int(seconds)
        if s < 60:
            return f"{s}s"
        m, s = divmod(s, 60)
        if m < 60:
            return f"{m}m {s}s"
        h, m = divmod(m, 60)
        return f"{h}h {m}m"

    def _tab_scroll(self, tab, padding="16"):
        """Cuerpo de pestaña con scroll vertical si no cabe."""
        scroll = ScrollableFrame(tab)
        scroll.pack(fill="both", expand=True)
        body = ttk.Frame(scroll.interior, padding=padding)
        body.pack(fill="both", expand=True)
        return body

    def setup_vault_tab(self):
        outer = self._tab_scroll(self.tab_vault, "20")

        page_header(
            outer,
            "Bóveda",
            "Ficha de la bóveda activa: trazabilidad, integridad y acciones de sesión.",
        ).pack(anchor="w", fill="x", pady=(0, 12))

        info = self.service.vault_info()

        grid = ttk.Frame(outer)
        grid.pack(fill="x")
        grid.columnconfigure(1, weight=1)

        ttk.Label(grid, text="Nombre", style="Bold.TLabel", font=T.FONT_BOLD).grid(
            row=0, column=0, sticky="nw", pady=3, padx=(0, 10)
        )
        ttk.Label(grid, text=info["name"]).grid(row=0, column=1, sticky="w", pady=3)
        ttk.Label(grid, text="Archivo", style="Bold.TLabel", font=T.FONT_BOLD).grid(
            row=1, column=0, sticky="nw", pady=3, padx=(0, 10)
        )
        ttk.Label(grid, text=info["path"], style="Hint.TLabel", wraplength=560, justify="left").grid(
            row=1, column=1, sticky="w", pady=3
        )
        ttk.Label(grid, text="Tamaño", style="Bold.TLabel", font=T.FONT_BOLD).grid(
            row=2, column=0, sticky="nw", pady=3, padx=(0, 10)
        )
        ttk.Label(grid, text=self._fmt_size(info["size"])).grid(row=2, column=1, sticky="w", pady=3)
        ttk.Label(grid, text="Creada", style="Bold.TLabel", font=T.FONT_BOLD).grid(
            row=3, column=0, sticky="nw", pady=3, padx=(0, 10)
        )
        ttk.Label(grid, text=info["created_at"] or "—").grid(row=3, column=1, sticky="w", pady=3)
        ttk.Label(grid, text="Modificada", style="Bold.TLabel", font=T.FONT_BOLD).grid(
            row=4, column=0, sticky="nw", pady=3, padx=(0, 10)
        )
        ttk.Label(grid, text=info["modified_at"] or "—").grid(row=4, column=1, sticky="w", pady=3)

        ttk.Label(grid, text="Descripción", style="Bold.TLabel", font=T.FONT_BOLD).grid(
            row=5, column=0, sticky="nw", pady=3, padx=(0, 10)
        )
        desc_box, self.desc_text = self._text_box(grid, height=4)
        desc_box.grid(row=5, column=1, sticky="ew", pady=3)
        self.desc_text.insert("1.0", info["description"] or "")
        RoundedButton(grid, text="Guardar descripción", command=self.save_description).grid(
            row=6, column=1, sticky="e", pady=4
        )

        ttk.Label(outer, text="Integridad (.gor)", style="Heading.TLabel", font=T.FONT_SUB).pack(
            anchor="w", pady=(16, 4)
        )
        hframe = ttk.Frame(outer)
        hframe.pack(fill="x")
        hframe.columnconfigure(1, weight=1)
        self.vault_md5 = tk.StringVar()
        self.vault_sha1 = tk.StringVar()
        self.vault_sha256 = tk.StringVar()
        self.vault_hash_status = tk.StringVar(value="")
        for i, (lab, var) in enumerate(
            [("MD5", self.vault_md5), ("SHA-1", self.vault_sha1), ("SHA-256", self.vault_sha256)]
        ):
            ttk.Label(hframe, text=lab, style="Bold.TLabel", font=T.FONT_BOLD).grid(
                row=i, column=0, sticky="w", pady=3, padx=(0, 10)
            )
            ttk.Entry(hframe, textvariable=var).grid(row=i, column=1, sticky="ew", pady=3)
            RoundedButton(hframe, text="Copiar", command=lambda v=var: self._copy_hash(v.get())).grid(
                row=i, column=2, padx=6
            )
        hbtns = ttk.Frame(outer)
        hbtns.pack(fill="x", pady=(6, 0))
        RoundedButton(hbtns, text="Calcular hash", command=self.compute_vault_hashes).pack(side="left", padx=4)
        ttk.Label(hbtns, textvariable=self.vault_hash_status, style="Hint.TLabel").pack(side="left", padx=8)

        ttk.Label(outer, text="Sesión", style="Heading.TLabel", font=T.FONT_SUB).pack(
            anchor="w", pady=(16, 4)
        )
        ab1 = ttk.Frame(outer)
        ab1.pack(fill="x", pady=3)
        RoundedButton(ab1, text="Cerrar sesión", command=self.logout).pack(side="left", padx=4)
        RoundedButton(ab1, text="Cambiar de bóveda", command=self.go_vault_selector).pack(side="left", padx=4)
        RoundedButton(ab1, text="Bloquear bóveda", command=self.lock_vault).pack(side="left", padx=4)
        ab2 = ttk.Frame(outer)
        ab2.pack(fill="x", pady=3)
        RoundedButton(ab2, text="Cambiar clave de bloqueo", command=self.change_lock_password).pack(side="left", padx=4)
        RoundedButton(ab2, text="Exportar bóveda", command=self.export_vault_backup).pack(side="left", padx=4)
        RoundedButton(ab2, text="Guardar ahora", command=self.save_vault_now).pack(side="left", padx=4)

    @staticmethod
    def _fmt_size(n: int) -> str:
        if n < 1024:
            return f"{n} B"
        value = float(n)
        for unit in ("KB", "MB", "GB", "TB"):
            value /= 1024
            if value < 1024 or unit == "TB":
                return f"{value:.1f} {unit}"
        return f"{n} B"

    def _text_box(self, parent, height: int = 5):
        """Text que respeta el ancho del padre (no desborda) + scroll vertical."""
        box = ttk.Frame(parent)
        box.columnconfigure(0, weight=1)
        box.rowconfigure(0, weight=1)
        text = tk.Text(
            box,
            height=height,
            width=1,
            bg=T.SURFACE,
            fg=T.FG,
            insertbackground=T.FG,
            highlightbackground=T.BORDER,
            highlightthickness=1,
            borderwidth=0,
            font=T.FONT,
            wrap="word",
            undo=True,
        )
        vsb = ttk.Scrollbar(box, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=vsb.set)
        text.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        return box, text

    def save_description(self):
        try:
            self.service.set_vault_description(self.desc_text.get("1.0", tk.END))
            messagebox.showinfo("Guardado", "Descripción actualizada.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def compute_vault_hashes(self):
        if getattr(self, "_vault_hash_busy", False):
            return
        self._vault_hash_busy = True
        self.vault_hash_status.set("Calculando…")
        self.vault_md5.set("")
        self.vault_sha1.set("")
        self.vault_sha256.set("")
        import threading

        result = {}

        def work():
            try:
                result.update(self.service.hash_vault_file())
            except Exception as e:
                result["_err"] = str(e)

        def poll():
            if "_err" in result:
                self._vault_hash_busy = False
                self.vault_hash_status.set("")
                messagebox.showerror("Error", result["_err"])
                return
            if result:
                self.vault_md5.set(result["md5"])
                self.vault_sha1.set(result["sha1"])
                self.vault_sha256.set(result["sha256"])
                self.vault_hash_status.set("Hash del .gor actual")
                self._vault_hash_busy = False
                return
            self.root.after(80, poll)

        threading.Thread(target=work, daemon=True).start()
        self.root.after(80, poll)

    def logout(self):
        if not messagebox.askyesno("Cerrar sesión", "¿Cerrar la sesión y salir de CryptoBro?"):
            return
        self.want_switch_vault = False
        try:
            self.service.lock()
        except Exception:
            pass
        self.root.destroy()

    def setup_encrypt_tab(self):
        """Configura los widgets de la pestaña de encriptación."""
        outer = self._tab_scroll(self.tab_encrypt, "20")
        page_header(
            outer,
            "Cifrar archivo",
            "Clave + opcional puzzle CPU (anti fuerza bruta). Con puzzle, la clave se guarda en la bóveda.",
        ).pack(anchor="w", fill="x", pady=(0, 14))

        frame = ttk.Frame(outer)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        # Selección de archivo
        self.enc_file_path = tk.StringVar()
        ttk.Label(frame, text="Archivo a cifrar", style="Bold.TLabel", font=T.FONT_BOLD).grid(
            row=0, column=0, sticky="w", pady=5
        )
        ttk.Entry(frame, textvariable=self.enc_file_path).grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        RoundedButton(frame, text="Examinar", command=self.browse_encrypt_file).grid(row=0, column=2, padx=5, pady=5)

        # Clave + ver + longitud + generar
        ttk.Label(frame, text="Clave de cifrado", style="Bold.TLabel", font=T.FONT_BOLD).grid(
            row=1, column=0, sticky="nw", pady=5
        )
        self.enc_key = tk.StringVar()
        self.enc_key_len = tk.IntVar(value=20)
        self.enc_show_key = tk.BooleanVar(value=False)
        key_box = ttk.Frame(frame)
        key_box.grid(row=1, column=1, columnspan=2, sticky="ew", pady=5, padx=5)
        key_box.columnconfigure(0, weight=1)

        key_row = ttk.Frame(key_box)
        key_row.grid(row=0, column=0, sticky="ew")
        key_row.columnconfigure(0, weight=1)
        self.entry_enc_key = ttk.Entry(key_row, textvariable=self.enc_key, show="*")
        self.entry_enc_key.grid(row=0, column=0, sticky="ew")
        RoundedButton(
            key_row, text="⚄ Generar", padx=10, pady=6, command=self._fill_random_encrypt_key
        ).grid(row=0, column=1, padx=(6, 0))

        opts = ttk.Frame(key_box)
        opts.grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Checkbutton(
            opts,
            text="Ver contraseña",
            variable=self.enc_show_key,
            command=self._toggle_enc_key_visibility,
        ).pack(side="left", padx=(0, 12))
        ttk.Label(opts, text="Longitud:").pack(side="left")
        ttk.Spinbox(
            opts, from_=8, to=128, textvariable=self.enc_key_len, width=5
        ).pack(side="left", padx=4)
        self.enc_key_entropy = tk.StringVar(value="")
        ttk.Label(opts, textvariable=self.enc_key_entropy, style="Hint.TLabel").pack(
            side="left", padx=(8, 0)
        )

        # Puzzle anti-bruteforce
        self.enc_use_puzzle = tk.BooleanVar(value=False)
        self.enc_puzzle_mins = tk.StringVar(value="0")
        self.enc_puzzle_secs = tk.StringVar(value="10")
        puzzle_row = ttk.Frame(frame)
        puzzle_row.grid(row=2, column=1, columnspan=2, sticky="w", pady=(8, 2), padx=5)
        ttk.Checkbutton(
            puzzle_row,
            text="Tiempo de descifrado (puzzle CPU)",
            variable=self.enc_use_puzzle,
            command=self._toggle_enc_puzzle,
        ).pack(side="left")
        ttk.Label(puzzle_row, text="Min").pack(side="left", padx=(12, 2))
        self.spin_enc_pmin = ttk.Spinbox(
            puzzle_row, from_=0, to=60, textvariable=self.enc_puzzle_mins, width=4
        )
        self.spin_enc_pmin.pack(side="left")
        ttk.Label(puzzle_row, text="Seg").pack(side="left", padx=(8, 2))
        self.spin_enc_psec = ttk.Spinbox(
            puzzle_row, from_=0, to=59, textvariable=self.enc_puzzle_secs, width=4
        )
        self.spin_enc_psec.pack(side="left")
        ttk.Label(
            frame,
            text="Al abrir: primero resuelve el puzzle, luego pide la contraseña. Requiere guardar en bóveda.",
            style="Hint.TLabel",
            wraplength=480,
        ).grid(row=3, column=1, columnspan=2, sticky="w", padx=5)

        # Guardar en bóveda
        self.store_key_var = tk.BooleanVar(value=True)
        self.cb_store_key = ttk.Checkbutton(
            frame,
            text="¿Guardar clave en la bóveda?",
            variable=self.store_key_var,
            command=self.toggle_encrypt_pass_info,
        )
        self.cb_store_key.grid(row=4, column=1, sticky="w", pady=(10, 5), padx=5)

        self.lbl_pass_title = ttk.Label(
            frame, text="Frase de recuperación", style="Bold.TLabel", font=T.FONT_BOLD
        )
        self.lbl_pass_info = ttk.Label(
            frame,
            text="Se generará automáticamente una frase memorable de 6 palabras.",
            style="Hint.TLabel",
            wraplength=400,
        )

        self.btn_action = RoundedButton(frame, text="Cifrar", command=self.perform_encryption)
        self.btn_action.grid(row=6, column=1, pady=(20, 6))

        self.enc_progress = ttk.Progressbar(frame, mode="determinate", maximum=100)
        self.enc_status = tk.StringVar(value="")
        self.enc_progress.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(4, 0))
        ttk.Label(frame, textvariable=self.enc_status, style="Hint.TLabel").grid(
            row=8, column=0, columnspan=3, sticky="w"
        )
        self.enc_progress.grid_remove()
        self._enc_busy = False

        self._toggle_enc_puzzle()
        self.toggle_encrypt_pass_info()

    def _toggle_enc_puzzle(self):
        on = self.enc_use_puzzle.get()
        state = "normal" if on else "disabled"
        self.spin_enc_pmin.config(state=state)
        self.spin_enc_psec.config(state=state)
        if on:
            self.store_key_var.set(True)
            self.toggle_encrypt_pass_info()

    def toggle_encrypt_pass_info(self):
        if self.enc_use_puzzle.get():
            self.store_key_var.set(True)
        if self.store_key_var.get():
            self.lbl_pass_title.grid(row=5, column=0, sticky="w", pady=5)
            self.lbl_pass_info.grid(row=5, column=1, pady=5, sticky="w", padx=5)
            self.btn_action.config(text="Cifrar y generar frase")
        else:
            self.lbl_pass_title.grid_remove()
            self.lbl_pass_info.grid_remove()
            self.btn_action.config(text="Solo cifrar")

    def browse_encrypt_file(self):
        filename = filedialog.askopenfilename()
        if filename:
            self.enc_file_path.set(filename)

    def _toggle_enc_key_visibility(self):
        self.entry_enc_key.config(show="" if self.enc_show_key.get() else "*")

    def _fill_random_encrypt_key(self):
        """Rellena la clave con CSPRNG; longitud según el spinbox."""
        try:
            length = int(self.enc_key_len.get())
            info = self.service.generate_password(length=length)
            self.enc_key.set(info["password"])
            self.enc_key_entropy.set(f"≈ {info['entropy_bits']} bits")
            self.root.clipboard_clear()
            self.root.clipboard_append(info["password"])
            self.enc_show_key.set(True)
            self._toggle_enc_key_visibility()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _set_enc_busy(self, busy: bool):
        self._enc_busy = busy
        self.btn_action.config(state="disabled" if busy else "normal")
        if busy:
            self.enc_progress.grid()
            self.enc_progress["value"] = 0
            self.enc_status.set("Cifrando…")
        else:
            self.enc_progress.grid_remove()
            self.enc_status.set("")

    def perform_encryption(self):
        if getattr(self, "_enc_busy", False):
            return
        file_path = self.enc_file_path.get()
        key = self.enc_key.get()
        store = self.store_key_var.get()
        use_puzzle = self.enc_use_puzzle.get()

        if not file_path or not key:
            messagebox.showerror("Error", "Selecciona un archivo e introduce una clave.")
            return
        if len(key) < 8:
            messagebox.showerror("Error", "La clave debe tener al menos 8 caracteres.")
            return

        puzzle_secs = 0
        if use_puzzle:
            try:
                puzzle_secs = int(self.enc_puzzle_mins.get() or 0) * 60 + int(
                    self.enc_puzzle_secs.get() or 0
                )
            except ValueError:
                messagebox.showerror("Error", "Tiempo de puzzle inválido")
                return
            if puzzle_secs <= 0:
                messagebox.showerror("Error", "Indica minutos y/o segundos de puzzle (> 0)")
                return
            if puzzle_secs > 3600:
                messagebox.showerror("Error", "Máximo 60 minutos de puzzle")
                return
            store = True

        import threading
        import queue
        import time

        self._set_enc_busy(True)
        q: queue.Queue = queue.Queue()
        t0 = time.monotonic()
        # con puzzle: clave aleatoria para el archivo; la del usuario envuelve tras el TLP
        file_key = self.service.generate_key() if use_puzzle else key
        generated = bool(use_puzzle)

        def on_progress(done, total):
            try:
                while True:
                    q.get_nowait()
            except queue.Empty:
                pass
            q.put(("prog", done, total, time.monotonic() - t0))

        def work():
            err = None
            result = None
            try:
                result = self.service.encryptFile(
                    file_path, file_key, generated=generated, progress=on_progress
                )
            except Exception as e:
                err = e
            q.put(("done", err, result))

        def finish_ok(extension, derived_key, bros_path):
            msg = (
                f"Archivo cifrado.\n"
                f"Salida (nombre opaco): {bros_path}\n"
                f"(El nombre original queda dentro del .bros)"
            )
            if use_puzzle:
                msg += f"\nPuzzle al abrir: ~{puzzle_secs}s de CPU, luego tu contraseña."
            try:
                if store:
                    while True:
                        passphrase = self.service.generate_mnemonic_passphrase(6)
                        hash_val = self.service.generate_hash(passphrase)
                        if not self.service.getItemByHash(hash_val):
                            break

                    to_store = derived_key
                    if use_puzzle:
                        to_store = self.service.seal_key_for_vault(
                            file_key, puzzle_secs, key
                        )

                    self.service.generate_and_store_key(
                        hash=hash_val, key=to_store, extension=extension, generated=True
                    )
                    msg += f"\n\nClave guardada en la bóveda.\nFRASE: {passphrase}"
                    if use_puzzle:
                        msg += "\n(Descifra con «Desde la bóveda» + frase; luego puzzle y contraseña.)"

                    if messagebox.askyesno(
                        "Guardar frase",
                        f"Tu frase de recuperación es:\n\n{passphrase}\n\n"
                        "¿Copiar al portapapeles y guardar en un archivo .par?\n\n"
                        "El .par se guarda CIFRADO con la clave de la bóveda (no en texto plano).",
                    ):
                        self.root.clipboard_clear()
                        self.root.clipboard_append(passphrase)
                        par_path = self.service.write_recovery_par(passphrase, bros_path)
                        msg += f"\nFrase copiada y guardada (cifrada) en: {par_path}"
                    else:
                        if messagebox.askyesno("Portapapeles", "¿Copiar la frase al portapapeles?"):
                            self.root.clipboard_clear()
                            self.root.clipboard_append(passphrase)
                            msg += "\nFrase copiada al portapapeles."
                        else:
                            msg += "\n(¡Anota tu frase!)"

                if messagebox.askyesno(
                    "¿Borrar original?", "Cifrado listo. ¿Borrar el archivo original (sin cifrar)?"
                ):
                    try:
                        from domain.cryptoBro import _shred_file

                        _shred_file(file_path)
                        msg += "\nArchivo original sobrescrito y eliminado."
                    except OSError as e:
                        msg += f"\nNo se pudo borrar el original: {e}"

                messagebox.showinfo("Listo", msg)
                self.refresh_keys_list()
                self.refresh_bodega_list()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        def poll():
            finished = False
            err = None
            result = None
            try:
                while True:
                    item = q.get_nowait()
                    if item[0] == "done":
                        finished = True
                        err = item[1]
                        result = item[2]
                    elif item[0] == "prog":
                        _, done, total, elapsed = item
                        total = max(total, 1)
                        pct = min(100, int(100 * done / total))
                        self.enc_progress["value"] = pct
                        rate = done / elapsed if elapsed > 0.2 else 0
                        eta = (total - done) / rate if rate > 0 else -1
                        self.enc_status.set(
                            f"Cifrando… {pct}% · {self._fmt_bytes(done)} / {self._fmt_bytes(total)}"
                            + (f" · ~{self._fmt_eta(eta)}" if eta >= 0 else "")
                        )
            except queue.Empty:
                pass
            if finished:
                self._set_enc_busy(False)
                if err:
                    messagebox.showerror("Error", str(err))
                elif result:
                    finish_ok(*result)
                return
            self.root.after(80, poll)

        threading.Thread(target=work, daemon=True).start()
        poll()

    def setup_decrypt_tab(self):
        outer = ttk.Frame(self.tab_decrypt, padding="20")
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)
        page_header(
            outer,
            "Descifrar archivo",
            "Elige de la bodega (o importa un .bros). Las cápsulas (.sbro) están en la pestaña Cápsulas.",
        ).pack(anchor="w", fill="x", pady=(0, 14))

        body = ttk.Frame(outer)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        left = ttk.Frame(body, padding=(0, 0, 10, 0))
        left.grid(row=0, column=0, sticky="nsw")
        ttk.Label(left, text="Bodega (.bros)", style="Heading.TLabel", font=T.FONT_SUB).pack(
            anchor="w", pady=(0, 6)
        )
        self.bodega_listbox = tk.Listbox(
            left, width=34, height=16,
            bg=T.SURFACE, fg=T.FG, selectbackground=T.SELECT, selectforeground=T.SELECT_FG,
            borderwidth=1, highlightthickness=1, highlightbackground=T.BORDER, font=T.FONT,
        )
        self.bodega_listbox.pack(fill="both", expand=True, pady=5)
        self.bodega_listbox.bind("<<ListboxSelect>>", self._on_bodega_select)
        bbtns = ttk.Frame(left)
        bbtns.pack(fill="x", pady=5)
        RoundedButton(bbtns, text="Actualizar", command=self.refresh_bodega_list).pack(fill="x", pady=2)
        RoundedButton(bbtns, text="Importar .bros", command=self.import_bros_to_bodega).pack(fill="x", pady=2)

        right_scroll = ScrollableFrame(body)
        right_scroll.grid(row=0, column=1, sticky="nsew")
        frame = right_scroll.interior
        frame.columnconfigure(1, weight=1)

        self.dec_file_path = tk.StringVar()
        ttk.Label(frame, text="Archivo (.bros)", style="Bold.TLabel", font=T.FONT_BOLD).grid(
            row=0, column=0, sticky="w", pady=5
        )
        ttk.Entry(frame, textvariable=self.dec_file_path).grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        RoundedButton(frame, text="Examinar", command=self.browse_decrypt_file).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(frame, text="Método", style="Heading.TLabel", font=T.FONT_SUB).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(12, 4)
        )
        self.dec_mode = tk.StringVar(value="manual")
        ttk.Radiobutton(frame, text="Clave manual", variable=self.dec_mode, value="manual", command=self.toggle_dec_inputs).grid(row=2, column=0, sticky="w", pady=5)
        ttk.Radiobutton(frame, text="Desde la bóveda", variable=self.dec_mode, value="db", command=self.toggle_dec_inputs).grid(row=2, column=1, sticky="w", pady=5)

        self.lbl_dec_key = ttk.Label(frame, text="Clave de descifrado", style="Bold.TLabel", font=T.FONT_BOLD)
        self.entry_dec_key = ttk.Entry(frame, show="*")

        self.lbl_dec_pass = ttk.Label(frame, text="Frase o archivo .par", style="Bold.TLabel", font=T.FONT_BOLD)
        self.pass_frame = ttk.Frame(frame)
        self.pass_frame.columnconfigure(0, weight=1)

        self.entry_dec_pass = ttk.Entry(self.pass_frame)
        self.entry_dec_pass.pack(side="left", padx=(0, 5), fill="x", expand=True)
        RoundedButton(self.pass_frame, text="Cargar .par", command=self.load_par_file).pack(side="left")

        self.toggle_dec_inputs()

        self.btn_decrypt = RoundedButton(frame, text="Descifrar", command=self.perform_decryption)
        self.btn_decrypt.grid(row=4, column=1, pady=(20, 6))

        self.dec_progress = ttk.Progressbar(frame, mode="determinate", maximum=100)
        self.dec_status = tk.StringVar(value="")
        self.dec_progress.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(4, 0))
        ttk.Label(frame, textvariable=self.dec_status, style="Hint.TLabel").grid(
            row=6, column=0, columnspan=3, sticky="w"
        )
        self.dec_progress.grid_remove()
        self._dec_busy = False

        self.refresh_bodega_list()

    def refresh_bodega_list(self):
        if not hasattr(self, "bodega_listbox"):
            return
        self._bodega_cache = self.service.list_bodega()
        self.bodega_listbox.delete(0, tk.END)
        for it in self._bodega_cache:
            self.bodega_listbox.insert(tk.END, it["original"])

    def _on_bodega_select(self, event=None):
        sel = self.bodega_listbox.curselection()
        if not sel:
            return
        it = self._bodega_cache[sel[0]]
        self.dec_file_path.set(it["path"])

    def import_bros_to_bodega(self):
        path = filedialog.askopenfilename(
            title="Importar archivo cifrado",
            filetypes=[("Archivos .bros", "*.bros"), ("Todos", "*.*")],
        )
        if not path:
            return
        if path.lower().endswith(".sbro"):
            messagebox.showinfo(
                "Cápsula",
                "Los .sbro son cápsulas. Usa la pestaña Cápsulas → Importar.",
            )
            return
        try:
            dest = self.service.import_bros_file(path)
            self.refresh_bodega_list()
            self.dec_file_path.set(dest)
            messagebox.showinfo("Importado", f"Archivo en la bodega:\n{dest}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_par_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Archivos .par", "*.par"), ("Texto", "*.txt")])
        if filename:
            try:
                content = self.service.read_recovery_par(filename)
                self.entry_dec_pass.delete(0, tk.END)
                self.entry_dec_pass.insert(0, content)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo leer el archivo: {e}")

    def browse_decrypt_file(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Archivos .bros", "*.bros"), ("Todos", "*.*")]
        )
        if filename:
            if filename.lower().endswith(".sbro"):
                messagebox.showinfo(
                    "Cápsula",
                    "Los .sbro se abren desde la pestaña Cápsulas.",
                )
                return
            self.dec_file_path.set(filename)

    def toggle_dec_inputs(self):
        if self.dec_mode.get() == "manual":
            if hasattr(self, 'lbl_dec_pass'):
                self.lbl_dec_pass.grid_remove()
                self.pass_frame.grid_remove()
            if hasattr(self, 'lbl_dec_key'):
                self.lbl_dec_key.grid(row=3, column=0, sticky="w", pady=5)
                self.entry_dec_key.grid(row=3, column=1, sticky="ew", pady=5, padx=5)
        else:
            if hasattr(self, 'lbl_dec_key'):
                self.lbl_dec_key.grid_remove()
                self.entry_dec_key.grid_remove()
            if hasattr(self, 'lbl_dec_pass'):
                self.lbl_dec_pass.grid(row=3, column=0, sticky="w", pady=5)
                self.pass_frame.grid(row=3, column=1, pady=5, sticky="ew", padx=5)

    def _set_dec_busy(self, busy: bool):
        self._dec_busy = busy
        self.btn_decrypt.config(state="disabled" if busy else "normal")
        if busy:
            self.dec_progress.grid()
            self.dec_progress["value"] = 0
            self.dec_status.set("Descifrando…")
        else:
            self.dec_progress.grid_remove()
            self.dec_status.set("")

    def perform_decryption(self):
        if getattr(self, "_dec_busy", False):
            return
        file_path = self.dec_file_path.get()
        mode = self.dec_mode.get()

        if not file_path:
            messagebox.showerror("Error", "Selecciona un archivo.")
            return
        if file_path.lower().endswith(".sbro"):
            messagebox.showinfo("Cápsula", "Abre los .sbro desde la pestaña Cápsulas.")
            return

        key = None
        extension = None
        generated = False
        sealed_blob = None

        try:
            if mode == "db":
                passphrase = self.entry_dec_pass.get()
                if not passphrase:
                    messagebox.showerror("Error", "Introduce la frase de recuperación.")
                    return
                hash_val = self.service.generate_hash(passphrase)
                item = self.service.getItemByHash(hash_val)

                if item:
                    extension = item.extension
                    from domain.timelock import is_puzzle

                    if is_puzzle(item.key):
                        sealed_blob = item.key
                        generated = True
                    else:
                        key = item.key
                        generated = True
                else:
                    messagebox.showerror("Error", "No hay clave para esta frase.")
                    return
            else:
                key = self.entry_dec_key.get()
                if not key:
                    messagebox.showerror("Error", "Introduce la clave.")
                    return
                from domain.timelock import is_puzzle

                if is_puzzle(key):
                    messagebox.showinfo(
                        "Puzzle",
                        "Esta clave está protegida con puzzle.\n"
                        "Usa «Desde la bóveda» con la frase de recuperación.",
                    )
                    return
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        import threading
        import queue
        import time
        from tkinter import simpledialog

        file_password = None
        if sealed_blob is not None:
            from domain.timelock import needs_password

            if needs_password(sealed_blob):
                file_password = simpledialog.askstring(
                    "Contraseña",
                    "Tras el puzzle se usará esta contraseña de cifrado:",
                    show="*",
                    parent=self.root,
                )
                if not file_password:
                    return

        self._set_dec_busy(True)
        q: queue.Queue = queue.Queue()
        t0 = time.monotonic()

        def on_file_progress(done, total):
            try:
                while True:
                    q.get_nowait()
            except queue.Empty:
                pass
            q.put(("fprog", done, total, time.monotonic() - t0))

        def on_puzzle_progress(done, total):
            try:
                while True:
                    q.get_nowait()
            except queue.Empty:
                pass
            q.put(("pprog", done, total))

        def work_full():
            err = None
            out = None
            try:
                use_key = key
                if sealed_blob is not None:
                    q.put(("status", "Resolviendo puzzle…"))
                    use_key = self.service.release_vault_key(
                        sealed_blob, password=file_password, progress=on_puzzle_progress
                    )
                q.put(("status", "Descifrando archivo…"))
                out = self.service.decryptFile(
                    file_path,
                    use_key,
                    extension=extension,
                    generated=generated,
                    progress=on_file_progress,
                )
            except Exception as e:
                err = e
            q.put(("done", err, out))

        def poll():
            finished = False
            err = None
            out = None
            try:
                while True:
                    item = q.get_nowait()
                    if item[0] == "done":
                        finished = True
                        err = item[1]
                        out = item[2]
                    elif item[0] == "status":
                        self.dec_status.set(item[1])
                    elif item[0] == "pprog":
                        _, done, total = item
                        total = max(total, 1)
                        pct = min(100, int(100 * done / total))
                        self.dec_progress["value"] = pct
                        self.dec_status.set(f"Puzzle… {pct}% ({done}/{total})")
                    elif item[0] == "fprog":
                        _, done, total, elapsed = item
                        total = max(total, 1)
                        pct = min(100, int(100 * done / total))
                        self.dec_progress["value"] = pct
                        rate = done / elapsed if elapsed > 0.2 else 0
                        eta = (total - done) / rate if rate > 0 else -1
                        self.dec_status.set(
                            f"Descifrando… {pct}% · {self._fmt_bytes(done)} / {self._fmt_bytes(total)}"
                            + (f" · ~{self._fmt_eta(eta)}" if eta >= 0 else "")
                        )
            except queue.Empty:
                pass
            if finished:
                self._set_dec_busy(False)
                if err:
                    messagebox.showerror("Error", f"Falló el descifrado: {err}")
                else:
                    messagebox.showinfo(
                        "Listo",
                        f"Descifrado correctamente:\n{out}\n\nEl archivo cifrado (.bros) se eliminó.",
                    )
                    self.refresh_bodega_list()
                return
            self.root.after(80, poll)

        threading.Thread(target=work_full, daemon=True).start()
        poll()


    def setup_hash_tab(self):
        frame = self._tab_scroll(self.tab_hash, "16")
        frame.columnconfigure(1, weight=1)

        page_header(
            frame,
            "Calculadora de hash",
            "Archivo, carpeta (manifiesto recursivo) o texto. "
            "MD5/SHA-1 = comprobación rápida; SHA-256 = mejor integridad.",
        ).grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 12))

        self.hash_mode = tk.StringVar(value="file")
        self._hash_busy = False
        ttk.Label(frame, text="Entrada", style="Heading.TLabel", font=T.FONT_SUB).grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(0, 4)
        )
        modes = ttk.Frame(frame)
        modes.grid(row=2, column=0, columnspan=3, sticky="w", pady=(0, 6))
        self.hash_radio_file = ttk.Radiobutton(
            modes, text="Archivo", variable=self.hash_mode, value="file", command=self._toggle_hash_mode
        )
        self.hash_radio_file.pack(side="left", padx=(0, 12))
        self.hash_radio_folder = ttk.Radiobutton(
            modes, text="Carpeta", variable=self.hash_mode, value="folder", command=self._toggle_hash_mode
        )
        self.hash_radio_folder.pack(side="left", padx=(0, 12))
        self.hash_radio_text = ttk.Radiobutton(
            modes, text="Texto", variable=self.hash_mode, value="text", command=self._toggle_hash_mode
        )
        self.hash_radio_text.pack(side="left")

        self.hash_path = tk.StringVar()
        self.lbl_hash_path = ttk.Label(frame, text="Ruta", style="Bold.TLabel", font=T.FONT_BOLD)
        self.entry_hash_path = ttk.Entry(frame, textvariable=self.hash_path)
        self.btn_hash_browse = RoundedButton(frame, text="Examinar", command=self._browse_hash_target)

        self.lbl_hash_text = ttk.Label(frame, text="Texto", style="Bold.TLabel", font=T.FONT_BOLD)
        self.hash_text = tk.Text(
            frame,
            height=6,
            bg=T.SURFACE,
            fg=T.FG,
            insertbackground=T.FG,
            highlightbackground=T.BORDER,
            highlightthickness=1,
            borderwidth=0,
            font=T.FONT,
        )

        self.hash_status = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self.hash_status, style="Hint.TLabel").grid(
            row=4, column=0, columnspan=3, sticky="w", pady=(4, 0)
        )

        self.hash_progress = ttk.Progressbar(frame, mode="determinate", maximum=100)
        self.hash_progress.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(6, 0))
        self.hash_progress.grid_remove()

        self.btn_hash_calc = RoundedButton(frame, text="Calcular", command=self.compute_hashes)
        self.btn_hash_calc.grid(row=6, column=1, sticky="e", pady=10)

        ttk.Label(frame, text="Resultados", style="Heading.TLabel", font=T.FONT_SUB).grid(
            row=7, column=0, columnspan=3, sticky="w", pady=(8, 4)
        )

        self.hash_md5 = tk.StringVar()
        self.hash_sha1 = tk.StringVar()
        self.hash_sha256 = tk.StringVar()
        for i, (lab, var) in enumerate(
            [("MD5", self.hash_md5), ("SHA-1", self.hash_sha1), ("SHA-256", self.hash_sha256)],
            start=8,
        ):
            ttk.Label(frame, text=lab, style="Bold.TLabel", font=T.FONT_BOLD).grid(
                row=i, column=0, sticky="w", pady=4
            )
            ent = ttk.Entry(frame, textvariable=var)
            ent.grid(row=i, column=1, sticky="ew", padx=4, pady=4)
            RoundedButton(
                frame, text="Copiar", command=lambda v=var: self._copy_hash(v.get())
            ).grid(row=i, column=2, padx=4)

        self._toggle_hash_mode()

    def setup_generator_tab(self):
        frame = self._tab_scroll(self.tab_gen, "16")
        frame.columnconfigure(1, weight=1)

        page_header(
            frame,
            "Generador de contraseñas",
            "Aleatoria segura (CSPRNG). Contraseña alfanumérica o frase de palabras. "
            "Entropía ≈ length × log₂(alfabeto). Objetivo práctico: ≥ 80 bits.",
        ).grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 12))

        self.gen_mode = tk.StringVar(value="password")
        ttk.Label(frame, text="Tipo", style="Heading.TLabel", font=T.FONT_SUB).grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(0, 4)
        )
        modes = ttk.Frame(frame)
        modes.grid(row=2, column=0, columnspan=3, sticky="w", pady=(0, 8))
        ttk.Radiobutton(
            modes, text="Contraseña", variable=self.gen_mode, value="password", command=self._toggle_gen_mode
        ).pack(side="left", padx=(0, 12))
        ttk.Radiobutton(
            modes, text="Frase (palabras)", variable=self.gen_mode, value="passphrase", command=self._toggle_gen_mode
        ).pack(side="left")

        self.gen_length = tk.IntVar(value=20)
        self.gen_words = tk.IntVar(value=8)
        self.gen_lower = tk.BooleanVar(value=True)
        self.gen_upper = tk.BooleanVar(value=True)
        self.gen_digits = tk.BooleanVar(value=True)
        self.gen_symbols = tk.BooleanVar(value=True)

        self.gen_opts = ttk.Frame(frame)
        self.gen_opts.grid(row=3, column=0, columnspan=3, sticky="ew", pady=4)

        self.lbl_gen_len = ttk.Label(self.gen_opts, text="Longitud", style="Bold.TLabel", font=T.FONT_BOLD)
        self.spin_gen_len = ttk.Spinbox(
            self.gen_opts, from_=8, to=128, textvariable=self.gen_length, width=6
        )
        self.chk_lower = ttk.Checkbutton(self.gen_opts, text="a-z", variable=self.gen_lower)
        self.chk_upper = ttk.Checkbutton(self.gen_opts, text="A-Z", variable=self.gen_upper)
        self.chk_digits = ttk.Checkbutton(self.gen_opts, text="0-9", variable=self.gen_digits)
        self.chk_symbols = ttk.Checkbutton(self.gen_opts, text="Símbolos", variable=self.gen_symbols)

        self.lbl_gen_words = ttk.Label(self.gen_opts, text="Palabras", style="Bold.TLabel", font=T.FONT_BOLD)
        self.spin_gen_words = ttk.Spinbox(
            self.gen_opts, from_=4, to=12, textvariable=self.gen_words, width=6
        )

        RoundedButton(frame, text="Generar", command=self._run_generator).grid(
            row=4, column=1, sticky="e", pady=12
        )

        self.gen_result = tk.StringVar()
        self.gen_entropy = tk.StringVar(value="")
        ttk.Label(frame, text="Resultado", style="Heading.TLabel", font=T.FONT_SUB).grid(
            row=5, column=0, columnspan=3, sticky="w", pady=(8, 4)
        )
        ttk.Entry(frame, textvariable=self.gen_result).grid(
            row=6, column=0, columnspan=2, sticky="ew", padx=(0, 4), pady=4
        )
        RoundedButton(frame, text="Copiar", command=lambda: self._copy_hash(self.gen_result.get())).grid(
            row=6, column=2, padx=4
        )
        ttk.Label(frame, textvariable=self.gen_entropy, style="Hint.TLabel").grid(
            row=7, column=0, columnspan=3, sticky="w", pady=(4, 0)
        )

        self._toggle_gen_mode()
        self._run_generator()

    def _toggle_gen_mode(self):
        for w in (
            self.lbl_gen_len,
            self.spin_gen_len,
            self.chk_lower,
            self.chk_upper,
            self.chk_digits,
            self.chk_symbols,
            self.lbl_gen_words,
            self.spin_gen_words,
        ):
            w.grid_forget()
        if self.gen_mode.get() == "password":
            self.lbl_gen_len.grid(row=0, column=0, sticky="w", padx=(0, 6))
            self.spin_gen_len.grid(row=0, column=1, sticky="w", padx=(0, 16))
            self.chk_lower.grid(row=0, column=2, padx=4)
            self.chk_upper.grid(row=0, column=3, padx=4)
            self.chk_digits.grid(row=0, column=4, padx=4)
            self.chk_symbols.grid(row=0, column=5, padx=4)
        else:
            self.lbl_gen_words.grid(row=0, column=0, sticky="w", padx=(0, 6))
            self.spin_gen_words.grid(row=0, column=1, sticky="w")

    def _run_generator(self):
        try:
            if self.gen_mode.get() == "passphrase":
                info = self.service.generate_passphrase_info(int(self.gen_words.get()))
            else:
                info = self.service.generate_password(
                    length=int(self.gen_length.get()),
                    lower=self.gen_lower.get(),
                    upper=self.gen_upper.get(),
                    digits=self.gen_digits.get(),
                    symbols=self.gen_symbols.get(),
                )
            self.gen_result.set(info["password"])
            bits = info["entropy_bits"]
            ok = "✓ fuerte" if bits >= 80 else ("aceptable" if bits >= 60 else "débil — sube longitud")
            kind = "palabras" if info.get("kind") == "passphrase" else "caracteres"
            self.gen_entropy.set(
                f"Entropía ≈ {bits} bits ({info['length']} {kind}, alfabeto {info['alphabet_size']}) — {ok}"
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _toggle_hash_mode(self):
        mode = self.hash_mode.get()
        if mode in ("file", "folder"):
            self.lbl_hash_text.grid_remove()
            self.hash_text.grid_remove()
            self.lbl_hash_path.config(text="Archivo:" if mode == "file" else "Carpeta:")
            self.lbl_hash_path.grid(row=3, column=0, sticky="w", pady=4)
            self.entry_hash_path.grid(row=3, column=1, sticky="ew", padx=4, pady=4)
            self.btn_hash_browse.grid(row=3, column=2, padx=4)
        else:
            self.lbl_hash_path.grid_remove()
            self.entry_hash_path.grid_remove()
            self.btn_hash_browse.grid_remove()
            self.lbl_hash_text.grid(row=3, column=0, sticky="nw", pady=4)
            self.hash_text.grid(row=3, column=1, columnspan=2, sticky="ew", padx=4, pady=4)

    def _browse_hash_target(self):
        if getattr(self, "_hash_busy", False):
            return
        mode = self.hash_mode.get()
        if mode == "folder":
            path = filedialog.askdirectory(title="Seleccionar carpeta")
        else:
            path = filedialog.askopenfilename(title="Seleccionar archivo")
        if path:
            self.hash_path.set(path)
            # no auto-calc: el usuario pulsa Calcular (carpetas grandes pueden tardar)

    def _copy_hash(self, value: str):
        if not value:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(value)

    def _set_hash_busy(self, busy: bool):
        self._hash_busy = busy
        state = "disabled" if busy else "normal"
        self.btn_hash_calc.config(state=state)
        self.btn_hash_browse.config(state=state)
        for rb in (self.hash_radio_file, self.hash_radio_folder, self.hash_radio_text):
            rb.config(state=state)
        self.entry_hash_path.config(state=state)
        self.hash_text.config(state=state)
        if busy:
            self.hash_progress.grid()
            self.hash_progress.configure(mode="indeterminate", value=0)
            self.hash_progress.start(12)
        else:
            self.hash_progress.stop()
            self.hash_progress.configure(mode="determinate", value=0)
            self.hash_progress.grid_remove()

    def _hash_set_progress(self, done: int, total: int, label: str = ""):
        total = max(total, 1)
        pct = min(100, int(100 * done / total))
        if str(self.hash_progress.cget("mode")) != "determinate":
            self.hash_progress.stop()
            self.hash_progress.configure(mode="determinate", maximum=100)
        self.hash_progress["value"] = pct
        if label:
            self.hash_status.set(f"{label} — {pct}%")
        else:
            self.hash_status.set(f"Calculando… {pct}%")

    def compute_hashes(self):
        if getattr(self, "_hash_busy", False):
            return

        mode = self.hash_mode.get()
        path = ""
        text = ""
        if mode == "file":
            path = self.hash_path.get().strip()
            if not path:
                messagebox.showerror("Error", "Selecciona un archivo")
                return
            if not os.path.isfile(path):
                messagebox.showerror("Error", f"No es un archivo:\n{path}")
                return
        elif mode == "folder":
            path = self.hash_path.get().strip()
            if not path:
                messagebox.showerror("Error", "Selecciona una carpeta")
                return
            if not os.path.isdir(path):
                messagebox.showerror("Error", f"No es una carpeta:\n{path}")
                return
        else:
            text = self.hash_text.get("1.0", tk.END)
            if text.endswith("\n"):
                text = text[:-1]

        import threading
        import queue

        self._set_hash_busy(True)
        self.hash_status.set("Calculando…")
        self.hash_md5.set("")
        self.hash_sha1.set("")
        self.hash_sha256.set("")
        q: queue.Queue = queue.Queue()

        def on_progress(done, total):
            try:
                while True:
                    q.get_nowait()
            except queue.Empty:
                pass
            q.put(("prog", done, total))

        def work():
            err = None
            result = None
            status = ""
            try:
                if mode == "file":
                    result = self.service.hash_file(path, progress=on_progress)
                    status = f"Archivo: {os.path.basename(path)}"
                elif mode == "folder":
                    result = self.service.hash_directory(path, progress=on_progress)
                    status = (
                        f"Carpeta: {result['files']} archivo(s) — hash del manifiesto ordenado"
                    )
                else:
                    data = text.encode("utf-8")
                    on_progress(0, 1)
                    result = self.service.hash_bytes(data)
                    on_progress(1, 1)
                    status = f"Texto: {len(data)} bytes"
            except Exception as e:
                err = e
            q.put(("done", err, result, status))

        def poll():
            finished = False
            err = None
            result = None
            status = ""
            latest = None
            try:
                while True:
                    item = q.get_nowait()
                    if item[0] == "done":
                        finished = True
                        err = item[1]
                        result = item[2]
                        status = item[3]
                    elif item[0] == "prog":
                        latest = (item[1], item[2])
            except queue.Empty:
                pass

            if latest is not None and not finished:
                done, total = latest
                if mode == "folder":
                    self._hash_set_progress(done, total, f"Archivo {done}/{total}")
                else:
                    self._hash_set_progress(done, total)

            if finished:
                self._set_hash_busy(False)
                if err:
                    self.hash_status.set("")
                    messagebox.showerror("Error", str(err))
                    return
                self.hash_md5.set(result["md5"])
                self.hash_sha1.set(result["sha1"])
                self.hash_sha256.set(result["sha256"])
                self.hash_status.set(status)
                return

            self.root.after(80, poll)

        threading.Thread(target=work, daemon=True).start()
        self.root.after(80, poll)

    def setup_keys_tab(self):
        frame = self._tab_scroll(self.tab_keys, "20")

        from domain.paths import get_workspace, cipher_dir, plain_dir

        page_header(
            frame,
            "Claves de la bóveda",
            "Huellas de frases guardadas y rutas de trabajo de esta sesión.",
        ).pack(anchor="w", fill="x", pady=(0, 12))

        ttk.Label(
            frame,
            text=f"Bóveda activa: {self.service.vault.name}",
            style="Heading.TLabel",
            font=T.FONT_SUB,
        ).pack(anchor="w", pady=(0, 4))
        ttk.Label(
            frame,
            text=f"Carpeta de trabajo: {get_workspace()}\n"
            f"Cifrados → {cipher_dir()}\n"
            f"Descifrados → {plain_dir()}",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(0, 10))

        ttk.Label(frame, text="Claves guardadas", style="Heading.TLabel", font=T.FONT_SUB).pack(
            anchor="w", pady=(0, 6)
        )

        columns = ("ID", "Hash", "Extension")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=12)
        self.tree.heading("ID", text="ID")
        self.tree.heading("Hash", text="Huella de la frase")
        self.tree.heading("Extension", text="Extensión")

        self.tree.column("ID", width=50)
        self.tree.column("Hash", width=300)
        self.tree.column("Extension", width=100)

        self.tree.pack(fill="x", expand=False)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)

        RoundedButton(btn_frame, text="Actualizar", command=self.refresh_keys_list).pack(
            side="left", padx=5
        )
        RoundedButton(btn_frame, text="Eliminar clave", command=self.delete_selected_key).pack(
            side="left", padx=5
        )
        RoundedButton(btn_frame, text="Exportar bóveda", command=self.export_vault_backup).pack(
            side="left", padx=5
        )
        RoundedButton(btn_frame, text="Guardar ahora", command=self.save_vault_now).pack(
            side="left", padx=5
        )

        vault_btns = ttk.Frame(frame)
        vault_btns.pack(pady=6)
        RoundedButton(
            vault_btns, text="Bloquear bóveda", command=self.lock_vault
        ).pack(side="left", padx=4)
        RoundedButton(
            vault_btns, text="Cambiar de bóveda", command=self.go_vault_selector
        ).pack(side="left", padx=4)
        RoundedButton(
            vault_btns, text="Cambiar clave de bloqueo", command=self.change_lock_password
        ).pack(side="left", padx=4)

        vault_btns2 = ttk.Frame(frame)
        vault_btns2.pack(pady=4)
        RoundedButton(
            vault_btns2, text="Vaciar bóveda", command=self.reset_current_vault
        ).pack(side="left", padx=4)
        RoundedButton(
            vault_btns2, text="Quitar bóveda", command=self.delete_current_vault
        ).pack(side="left", padx=4)

        self.refresh_keys_list()

    def save_vault_now(self):
        try:
            self.service.save_vault_now()
            messagebox.showinfo("Guardado", "Bóveda guardada en disco.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def lock_vault(self):
        """Cierra la sesión y vuelve al selector de bóvedas."""
        if not messagebox.askyesno(
            "Bloquear",
            "¿Bloquear esta bóveda y volver a la pantalla de inicio?",
        ):
            return
        self.want_switch_vault = True
        try:
            self.service.lock()
        except Exception:
            pass
        self.root.destroy()

    def go_vault_selector(self):
        """Salir de esta bóveda (mismo efecto que bloquear)."""
        self.lock_vault()

    def change_lock_password(self):
        from tkinter import simpledialog

        old = simpledialog.askstring("Clave actual", "Clave de bloqueo actual:", show="*", parent=self.root)
        if not old:
            return
        new = simpledialog.askstring("Nueva clave", "Nueva clave (mín. 8):", show="*", parent=self.root)
        if not new:
            return
        new2 = simpledialog.askstring("Confirmar", "Repite la nueva clave:", show="*", parent=self.root)
        if new != new2:
            messagebox.showerror("Error", "Las claves no coinciden")
            return
        try:
            self.service.change_vault_password(old, new)
            messagebox.showinfo("Listo", "Clave de bloqueo actualizada.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def reset_current_vault(self):
        from tkinter import simpledialog

        if not messagebox.askyesno(
            "Vaciar bóveda",
            "¿Borrar TODO el contenido de esta bóveda (notas, claves, cápsulas)\n"
            "manteniendo el mismo nombre y clave?\n\nNo se puede deshacer.",
        ):
            return
        pw = simpledialog.askstring("Confirmar", "Clave de bloqueo:", show="*", parent=self.root)
        if not pw:
            return
        try:
            self.service.reset_vault_contents(pw)
            self.refresh_keys_list()
            if hasattr(self, "refresh_messages_list"):
                self.refresh_messages_list()
            if hasattr(self, "refresh_capsules"):
                self.refresh_capsules()
            messagebox.showinfo("Listo", "Bóveda vaciada.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_current_vault(self):
        name = self.service.vault.name
        if not messagebox.askyesno(
            "Quitar bóveda",
            f"¿Quitar «{name}» de la lista?\n\n"
            "El archivo .gor seguirá en disco (puedes importarlo otra vez).",
        ):
            return
        wipe = messagebox.askyesno(
            "¿Eliminar del disco?",
            f"¿Quieres también borrar el archivo .gor de «{name}»?\n\n"
            "Sí = eliminarla por completo (irreversible).\n"
            "No = solo quitarla de la lista.",
        )
        try:
            self.service.delete_current_vault(wipe_file=wipe)
            if wipe:
                messagebox.showinfo("Eliminada", f"«{name}» borrada del disco.")
            else:
                messagebox.showinfo(
                    "Lista",
                    f"«{name}» quitada de la lista.\nEl .gor sigue en la carpeta de trabajo.",
                )
            self.want_switch_vault = True
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def export_vault_backup(self):
        path = filedialog.asksaveasfilename(
            title="Exportar bóveda",
            defaultextension=".gor",
            filetypes=[
                ("Bóveda CryptoBro", "*.gor"),
                ("Copia antigua", "*.cbvault"),
            ],
            initialfile=f"{self.service.vault.name}.gor",
        )
        if not path:
            return
        try:
            out = self.service.export_vault_backup(path)
            messagebox.showinfo(
                "Copia lista",
                f"Exportado a:\n{out}\n\n"
                "Un solo archivo .gor (sigue cifrado). Misma clave de bloqueo para abrirlo.",
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def delete_selected_key(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecciona una clave para eliminar.")
            return
            
        if messagebox.askyesno("Confirmar", "¿Seguro que quieres eliminar esta clave?"):
            try:
                item_values = self.tree.item(selected_item, 'values')
                item_id = item_values[0]
                self.service.delete_key_by_id(item_id)
                self.refresh_keys_list()
                messagebox.showinfo("Listo", "Clave eliminada.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar: {e}")

    def refresh_keys_list(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        items = self.service.getAllItems()
        for item in items:
            self.tree.insert('', 'end', values=(item.id, item.hash, item.extension))


    # --- Cápsulas temporales (soft lock) ---
    def setup_capsules_tab(self):
        frame = ttk.Frame(self.tab_capsules, padding="12")
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)

        ttk.Label(
            frame,
            text="Cápsulas temporales",
            style="Page.TLabel",
            font=T.FONT_PAGE,
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            frame,
            text="Las cápsulas se guardan en la bóveda (no en data/). Exportar → archivo .sbro portátil.\n"
            "1) Tiempo a bloquear: espera de calendario hasta poder abrir (reloj del PC).\n"
            "2) Tiempo de descifrado: al Resolver, la CPU trabaja esos min/seg (puzzle).\n"
            "3) Contraseña (opcional): tras calendario/puzzle, pide clave para descifrar. "
            "Puedes combinar las tres capas.",
            style="Hint.TLabel",
            wraplength=760,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 10))

        body = ttk.Frame(frame)
        body.grid(row=2, column=0, sticky="nsew")
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        form_scroll = ScrollableFrame(body)
        form_scroll.grid(row=0, column=0, sticky="nsw")
        form = ttk.Frame(form_scroll.interior, padding=8)
        form.pack(fill="both", expand=True)
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Archivo", style="Bold.TLabel", font=T.FONT_BOLD).grid(
            row=0, column=0, sticky="w", pady=3
        )
        self.cap_file = tk.StringVar()
        ttk.Entry(form, textvariable=self.cap_file, width=28).grid(row=0, column=1, sticky="ew", padx=4)
        RoundedButton(form, text="…", padx=10, pady=6, command=self._browse_capsule_file).grid(row=0, column=2)

        ttk.Label(form, text="Etiqueta", style="Bold.TLabel", font=T.FONT_BOLD).grid(
            row=1, column=0, sticky="w", pady=3
        )
        self.cap_label = tk.StringVar()
        ttk.Entry(form, textvariable=self.cap_label).grid(row=1, column=1, columnspan=2, sticky="ew", padx=4)

        ttk.Label(form, text="Tiempo a bloquear", style="Heading.TLabel", font=T.FONT_SUB).grid(
            row=2, column=0, columnspan=3, sticky="w", pady=(14, 2)
        )
        ttk.Label(
            form, text="Espera hasta esa fecha antes de poder Resolver/Desbloquear.", style="Hint.TLabel"
        ).grid(row=3, column=0, columnspan=3, sticky="w")

        self.cap_years = tk.StringVar(value="0")
        self.cap_days = tk.StringVar(value="0")
        self.cap_hours = tk.StringVar(value="0")
        self.cap_lock_mins = tk.StringVar(value="0")
        lock_row = ttk.Frame(form)
        lock_row.grid(row=4, column=0, columnspan=3, sticky="w", pady=4)
        for i, (lab, var) in enumerate(
            [
                ("Años", self.cap_years),
                ("Días", self.cap_days),
                ("Horas", self.cap_hours),
                ("Min", self.cap_lock_mins),
            ]
        ):
            ttk.Label(lock_row, text=lab).grid(row=0, column=i)
            ttk.Entry(lock_row, textvariable=var, width=5).grid(row=1, column=i, padx=2)

        ttk.Label(form, text="Tiempo de descifrado", style="Heading.TLabel", font=T.FONT_SUB).grid(
            row=5, column=0, columnspan=3, sticky="w", pady=(14, 2)
        )
        ttk.Label(
            form, text="Trabajo de CPU al Resolver (máx. 60 min). 0 = solo calendario.", style="Hint.TLabel"
        ).grid(row=6, column=0, columnspan=3, sticky="w")

        self.cap_dec_mins = tk.StringVar(value="0")
        self.cap_dec_secs = tk.StringVar(value="10")
        dec_row = ttk.Frame(form)
        dec_row.grid(row=7, column=0, columnspan=3, sticky="w", pady=4)
        for i, (lab, var) in enumerate(
            [("Min", self.cap_dec_mins), ("Seg", self.cap_dec_secs)]
        ):
            ttk.Label(dec_row, text=lab).grid(row=0, column=i)
            ttk.Entry(dec_row, textvariable=var, width=5).grid(row=1, column=i, padx=2)

        # compat: aliases por si algo viejo referencia cap_mins/secs
        self.cap_mins = self.cap_dec_mins
        self.cap_secs = self.cap_dec_secs

        self.cap_del_orig = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            form, text="Borrar original tras cifrar", variable=self.cap_del_orig
        ).grid(row=8, column=1, columnspan=2, sticky="w", pady=6)

        self.cap_use_pw = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            form,
            text="Requerir contraseña al abrir (opcional)",
            variable=self.cap_use_pw,
            command=self._toggle_cap_password,
        ).grid(row=9, column=0, columnspan=3, sticky="w", pady=(8, 2))

        self.cap_pw = tk.StringVar()
        self.cap_pw2 = tk.StringVar()
        self.lbl_cap_pw = ttk.Label(form, text="Contraseña", style="Bold.TLabel", font=T.FONT_BOLD)
        self.entry_cap_pw = ttk.Entry(form, textvariable=self.cap_pw, show="*")
        self.lbl_cap_pw2 = ttk.Label(form, text="Repetir", style="Bold.TLabel", font=T.FONT_BOLD)
        self.entry_cap_pw2 = ttk.Entry(form, textvariable=self.cap_pw2, show="*")
        self._toggle_cap_password()

        self.btn_create_capsule = RoundedButton(
            form, text="Crear cápsula", command=self.create_capsule
        )
        self.btn_create_capsule.grid(row=12, column=1, sticky="e", pady=(10, 2))
        self.cap_status = tk.StringVar(value="")
        ttk.Label(form, textvariable=self.cap_status, style="Hint.TLabel").grid(
            row=13, column=0, columnspan=3, sticky="w"
        )
        self.cap_progress = ttk.Progressbar(form, mode="determinate", maximum=100)
        self.cap_progress.grid(row=14, column=0, columnspan=3, sticky="ew", pady=(2, 0))
        self.cap_progress.grid_remove()
        self._cap_busy = False

        right = ttk.Frame(body, padding=8)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        ttk.Label(right, text="Tus cápsulas", style="Heading.TLabel", font=T.FONT_SUB).grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        cols = ("id", "label", "bloqueo", "descifrado", "path")
        self.cap_tree = ttk.Treeview(right, columns=cols, show="headings", height=10)
        self.cap_tree.heading("id", text="ID")
        self.cap_tree.heading("label", text="Etiqueta")
        self.cap_tree.heading("bloqueo", text="Bloqueo")
        self.cap_tree.heading("descifrado", text="Descifrado")
        self.cap_tree.heading("path", text="Archivo")
        self.cap_tree.column("id", width=36)
        self.cap_tree.column("label", width=100)
        self.cap_tree.column("bloqueo", width=110)
        self.cap_tree.column("descifrado", width=90)
        self.cap_tree.column("path", width=180)
        self.cap_tree.grid(row=1, column=0, sticky="nsew")
        self.cap_tree.bind("<<TreeviewSelect>>", self._on_capsule_select)

        anim = ttk.Frame(right)
        anim.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self.cap_timer_canvas = tk.Canvas(
            anim, width=96, height=96, bg=T.BG, highlightthickness=0
        )
        self.cap_timer_canvas.pack(side="left", padx=(0, 12))
        self.cap_timer_text = tk.StringVar(value="Selecciona una cápsula")
        self.cap_timer_sub = tk.StringVar(value="")
        txt = ttk.Frame(anim)
        txt.pack(side="left", fill="x", expand=True)
        ttk.Label(txt, textvariable=self.cap_timer_text, style="Timer.TLabel", font=T.FONT_TIMER).pack(
            anchor="w"
        )
        ttk.Label(txt, textvariable=self.cap_timer_sub, style="Hint.TLabel").pack(anchor="w")
        self._cap_anim_totals = {}

        btns = ttk.Frame(right)
        btns.grid(row=3, column=0, sticky="ew", pady=8)
        self.btn_unlock_cap = RoundedButton(
            btns, text="Resolver / Desbloquear", command=self.unlock_selected_capsule, state="disabled"
        )
        self.btn_unlock_cap.pack(side="left", padx=4)
        RoundedButton(btns, text="Actualizar", command=self.refresh_capsules).pack(side="left", padx=4)
        RoundedButton(btns, text="Eliminar", command=self.delete_selected_capsule).pack(side="left", padx=4)
        RoundedButton(btns, text="Exportar", command=self.export_selected_capsule).pack(side="left", padx=4)
        RoundedButton(btns, text="Importar", command=self.import_capsule).pack(side="left", padx=4)

        self._draw_cap_timer(None)
        self.refresh_capsules()
        self._capsule_tick()

    def _browse_capsule_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.cap_file.set(path)

    def _toggle_cap_password(self):
        if self.cap_use_pw.get():
            self.lbl_cap_pw.grid(row=10, column=0, sticky="w", pady=2)
            self.entry_cap_pw.grid(row=10, column=1, columnspan=2, sticky="ew", padx=4, pady=2)
            self.lbl_cap_pw2.grid(row=11, column=0, sticky="w", pady=2)
            self.entry_cap_pw2.grid(row=11, column=1, columnspan=2, sticky="ew", padx=4, pady=2)
        else:
            self.lbl_cap_pw.grid_remove()
            self.entry_cap_pw.grid_remove()
            self.lbl_cap_pw2.grid_remove()
            self.entry_cap_pw2.grid_remove()
            self.cap_pw.set("")
            self.cap_pw2.set("")

    def _parse_int(self, var, name):
        try:
            v = int(var.get().strip() or "0")
            if v < 0:
                raise ValueError
            return v
        except ValueError as e:
            raise ValueError(f"{name} inválido") from e

    def _cap_is_puzzle(self, cap) -> bool:
        from domain.timelock import is_puzzle

        return is_puzzle(cap.key)

    def _cap_needs_password(self, cap) -> bool:
        from domain.timelock import needs_password

        return needs_password(cap.key)

    def _cap_decrypt_label(self, cap) -> str:
        parts = []
        if self._cap_is_puzzle(cap):
            import json

            try:
                parts.append(self._fmt_cpu(int(json.loads(cap.key).get("secs", 0))))
            except Exception:
                parts.append("puzzle")
        else:
            parts.append("inmediato")
        if self._cap_needs_password(cap):
            parts.append("+ clave")
        return " ".join(parts)

    def _cap_lock_label(self, cap) -> str:
        label, ready, _ = self._format_cal_remaining(cap.unlock_at)
        return "LISTO" if ready else label

    @staticmethod
    def _fmt_cpu(secs: int) -> str:
        if secs <= 0:
            return "—"
        if secs < 60:
            return f"~{secs}s CPU"
        return f"~{secs // 60} min CPU"

    def _format_cal_remaining(self, unlock_at_iso: str):
        from datetime import datetime

        unlock_at = datetime.fromisoformat(unlock_at_iso)
        rem = unlock_at - datetime.now()
        secs_left = rem.total_seconds()
        if secs_left <= 0:
            return "LISTO", True, 0.0
        total = int(secs_left)
        years, rem_s = divmod(total, 365 * 24 * 3600)
        days, rem_s = divmod(rem_s, 24 * 3600)
        hours, rem_s = divmod(rem_s, 3600)
        mins, secs = divmod(rem_s, 60)
        parts = []
        if years:
            parts.append(f"{years}a")
        if days:
            parts.append(f"{days}d")
        parts.append(f"{hours:02d}:{mins:02d}:{secs:02d}")
        return " ".join(parts), False, secs_left

    def create_capsule(self):
        if getattr(self, "_cap_busy", False):
            return
        path = self.cap_file.get().strip()
        if not path:
            messagebox.showerror("Error", "Selecciona un archivo")
            return
        password = None
        if self.cap_use_pw.get():
            password = self.cap_pw.get()
            if password != self.cap_pw2.get():
                messagebox.showerror("Error", "Las contraseñas no coinciden")
                return
            if len(password) < 8:
                messagebox.showerror("Error", "La contraseña debe tener al menos 8 caracteres")
                return

        try:
            years = self._parse_int(self.cap_years, "Años")
            days = self._parse_int(self.cap_days, "Días")
            hours = self._parse_int(self.cap_hours, "Horas")
            lock_minutes = self._parse_int(self.cap_lock_mins, "Min bloqueo")
            decrypt_minutes = self._parse_int(self.cap_dec_mins, "Min descifrado")
            decrypt_seconds = self._parse_int(self.cap_dec_secs, "Seg descifrado")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        import threading
        import queue
        import time

        label = self.cap_label.get()
        delete_original = self.cap_del_orig.get()
        self._cap_busy = True
        self.btn_create_capsule.config(state="disabled")
        self.cap_progress.grid()
        self.cap_progress["value"] = 0
        self.cap_status.set("Cifrando cápsula…")
        q: queue.Queue = queue.Queue()
        t0 = time.monotonic()

        def on_progress(done, total):
            try:
                while True:
                    q.get_nowait()
            except queue.Empty:
                pass
            q.put(("prog", done, total, time.monotonic() - t0))

        def work():
            err = None
            result = None
            try:
                result = self.service.create_time_capsule(
                    file_path=path,
                    label=label,
                    years=years,
                    days=days,
                    hours=hours,
                    lock_minutes=lock_minutes,
                    decrypt_minutes=decrypt_minutes,
                    decrypt_seconds=decrypt_seconds,
                    delete_original=delete_original,
                    password=password,
                    progress=on_progress,
                )
            except Exception as e:
                err = e
            q.put(("done", err, result))

        def poll():
            finished = False
            err = None
            result = None
            try:
                while True:
                    item = q.get_nowait()
                    if item[0] == "done":
                        finished = True
                        err = item[1]
                        result = item[2]
                    elif item[0] == "prog":
                        _, done, total, elapsed = item
                        total = max(total, 1)
                        pct = min(100, int(100 * done / total))
                        self.cap_progress["value"] = pct
                        rate = done / elapsed if elapsed > 0.2 else 0
                        eta = (total - done) / rate if rate > 0 else -1
                        self.cap_status.set(
                            f"Cifrando… {pct}% · {self._fmt_bytes(done)} / {self._fmt_bytes(total)}"
                            + (f" · ~{self._fmt_eta(eta)}" if eta >= 0 else "")
                        )
            except queue.Empty:
                pass
            if finished:
                self._cap_busy = False
                self.btn_create_capsule.config(state="normal")
                self.cap_progress.grid_remove()
                self.cap_status.set("")
                if err:
                    messagebox.showerror("Error", str(err))
                    return
                cid, unlock_at, bros, lock_secs, dec_secs, use_pw = result
                parts = [f"ID {cid}"]
                if lock_secs > 0:
                    parts.append(f"Bloqueo hasta:\n{unlock_at}")
                else:
                    parts.append("Sin espera de calendario (puedes Resolver ya).")
                if dec_secs > 0:
                    parts.append(f"Descifrado: {self._fmt_cpu(dec_secs)} al Resolver")
                else:
                    parts.append("Descifrado: inmediato (sin puzzle)")
                if use_pw:
                    parts.append("Contraseña: sí (se pedirá tras calendario/puzzle)")
                else:
                    parts.append("Contraseña: no")
                parts.append(f"Archivo (.sbro):\n{bros}")
                messagebox.showinfo("Cápsula creada", "\n\n".join(parts))
                if lock_secs > 0:
                    self._cap_anim_totals[cid] = max(lock_secs, 1.0)
                self.cap_file.set("")
                self.cap_pw.set("")
                self.cap_pw2.set("")
                self.refresh_capsules()
                if self.cap_tree.exists(str(cid)):
                    self.cap_tree.selection_set(str(cid))
                    self._on_capsule_select()
                return
            self.root.after(80, poll)

        threading.Thread(target=work, daemon=True).start()
        poll()

    def _draw_cap_timer(self, cap, frac=None, status=None):
        import math

        c = self.cap_timer_canvas
        c.delete("all")
        pad, size = 8, 96
        x0, y0, x1, y1 = pad, pad, size - pad, size - pad
        c.create_oval(x0, y0, x1, y1, outline=T.BORDER, width=8)
        if cap is None and frac is None:
            self.cap_timer_text.set("Selecciona una cápsula")
            self.cap_timer_sub.set("Bloqueo (calendario) + descifrado (CPU)")
            return

        if frac is not None:
            extent = -360.0 * max(0.0, min(1.0, frac))
            c.create_arc(
                x0, y0, x1, y1, start=90, extent=extent, style="arc", outline=T.ACCENT, width=9
            )
            ang = math.radians(90 + extent)
            cx = cy = size / 2
            r = (size - pad * 2) / 2
            px, py = cx + r * math.cos(ang), cy - r * math.sin(ang)
            c.create_oval(px - 4, py - 4, px + 4, py + 4, fill=T.ACCENT, outline="")
            self.cap_timer_text.set(status or f"{int(frac * 100)}%")
            self.cap_timer_sub.set("Resolviendo puzzle de descifrado…")
            return

        label, ready, secs_left = self._format_cal_remaining(cap.unlock_at)
        dec = self._cap_decrypt_label(cap)

        if not ready:
            totals = getattr(self, "_cap_anim_totals", {})
            if cap.id not in totals:
                totals[cap.id] = max(secs_left, 1.0)
                self._cap_anim_totals = totals
            frac_c = max(0.0, min(1.0, secs_left / totals[cap.id]))
            extent = -360.0 * frac_c
            pulse = 8 + (1 if int(secs_left) % 2 == 0 else 0)
            c.create_arc(
                x0, y0, x1, y1, start=90, extent=extent, style="arc", outline=T.ACCENT, width=pulse
            )
            ang = math.radians(90 + extent)
            cx = cy = size / 2
            r = (size - pad * 2) / 2
            px, py = cx + r * math.cos(ang), cy - r * math.sin(ang)
            c.create_oval(px - 4, py - 4, px + 4, py + 4, fill=T.ACCENT, outline="")
            self.cap_timer_text.set(label)
            self.cap_timer_sub.set(f"Bloqueada · luego descifrado {dec}")
            return

        # calendario cumplido
        c.create_oval(x0, y0, x1, y1, outline=T.OK, width=8)
        pw_note = " · luego contraseña" if self._cap_needs_password(cap) else ""
        if self._cap_is_puzzle(cap):
            c.create_text(size // 2, size // 2, text="▶", fill=T.OK, font=("DejaVu Sans", 28, "bold"))
            self.cap_timer_text.set("Listo para Resolver")
            self.cap_timer_sub.set(f"Descifrado: {dec}{pw_note}")
        else:
            c.create_text(size // 2, size // 2, text="✓", fill=T.OK, font=("DejaVu Sans", 28, "bold"))
            self.cap_timer_text.set("LISTO")
            self.cap_timer_sub.set(
                "Desbloqueo inmediato" + (" · pide contraseña" if self._cap_needs_password(cap) else "")
            )

    def refresh_capsules(self):
        if not hasattr(self, "cap_tree"):
            return
        sel = self.cap_tree.selection()
        for i in self.cap_tree.get_children():
            self.cap_tree.delete(i)
        self._capsules_cache = self.service.get_all_capsules()
        for c in self._capsules_cache:
            _, ready, _ = self._format_cal_remaining(c.unlock_at)
            path_disp = c.bros_path or ""
            if ".cb_capsules" in path_disp.replace("\\", "/"):
                path_disp = "en bóveda"
            else:
                path_disp = os.path.basename(path_disp) or path_disp
            self.cap_tree.insert(
                "",
                "end",
                iid=str(c.id),
                values=(
                    c.id,
                    c.label,
                    self._cap_lock_label(c),
                    self._cap_decrypt_label(c),
                    path_disp,
                ),
                tags=("ready",) if ready else ("locked",),
            )
        self.cap_tree.tag_configure("ready", foreground=T.OK)
        self.cap_tree.tag_configure("locked", foreground=T.FG_MUTED)
        if sel and self.cap_tree.exists(sel[0]):
            self.cap_tree.selection_set(sel[0])
            self.cap_tree.focus(sel[0])
        self._on_capsule_select()

    def _capsule_tick(self):
        if not getattr(self, "_cap_unlocking", False):
            self.refresh_capsules()
        self.root.after(1000, self._capsule_tick)

    def _on_capsule_select(self, event=None):
        sel = self.cap_tree.selection() if hasattr(self, "cap_tree") else ()
        unlocking = getattr(self, "_cap_unlocking", False)
        if not sel:
            self.btn_unlock_cap.config(state="disabled")
            self._draw_cap_timer(None)
            return
        cid = int(sel[0])
        cap = next((c for c in getattr(self, "_capsules_cache", []) if c.id == cid), None)
        if not cap:
            self.btn_unlock_cap.config(state="disabled")
            self._draw_cap_timer(None)
            return

        _, ready, _ = self._format_cal_remaining(cap.unlock_at)
        if self._cap_is_puzzle(cap):
            self.btn_unlock_cap.config(text="Resolver")
        else:
            self.btn_unlock_cap.config(text="Desbloquear")
        self.btn_unlock_cap.config(
            state="disabled" if (unlocking or not ready) else "normal"
        )
        if not unlocking:
            self._draw_cap_timer(cap)

    def _ask_capsule_password(self) -> str | None:
        from tkinter import simpledialog

        return simpledialog.askstring(
            "Contraseña de la cápsula",
            "Introduce la contraseña para descifrar:",
            show="*",
            parent=self.root,
        )

    def _finish_capsule_open(self, cid: int, secret: str) -> None:
        from domain.timelock import is_password_wrap

        password = None
        if is_password_wrap(secret):
            password = self._ask_capsule_password()
            if not password:
                messagebox.showinfo(
                    "Cancelado",
                    "Se liberó el tiempo/puzzle, pero falta la contraseña para descifrar.",
                )
                self._on_capsule_select()
                return
        try:
            out = self.service.open_capsule_with_secret(cid, secret, password=password)
            messagebox.showinfo(
                "Listo",
                f"Cápsula desbloqueada.\nArchivo:\n{out}\n\n"
                "El .sbro permanece en disco. Usa Eliminar si quieres quitarlo de la lista.",
            )
            self.refresh_capsules()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self._on_capsule_select()

    def unlock_selected_capsule(self):
        import threading
        import queue
        from domain.timelock import is_puzzle

        sel = self.cap_tree.selection()
        if not sel or getattr(self, "_cap_unlocking", False):
            return
        cid = int(sel[0])
        cap = next((c for c in getattr(self, "_capsules_cache", []) if c.id == cid), None)
        if not cap:
            return

        _, ready, _ = self._format_cal_remaining(cap.unlock_at)
        if not ready:
            messagebox.showerror("Bloqueada", f"Aún no: espera hasta\n{cap.unlock_at}")
            return

        # Solo calendario (sin puzzle): pide contraseña si aplica y abre
        if not is_puzzle(cap.key):
            try:
                secret = self.service.release_capsule_secret(cid)
                self._finish_capsule_open(cid, secret)
            except Exception as e:
                messagebox.showerror("Error", str(e))
            return

        self._cap_unlocking = True
        self.btn_unlock_cap.config(state="disabled")
        self._draw_cap_timer(None, frac=0.0, status="0%")
        q: queue.Queue = queue.Queue()

        def on_progress(done, total):
            try:
                while True:
                    q.get_nowait()
            except queue.Empty:
                pass
            q.put(("prog", done, total))

        def work():
            err = None
            secret = None
            try:
                # No tocar SQLite desde el worker: cap ya viene del cache del hilo GUI
                if is_puzzle(cap.key):
                    from domain.timelock import open_puzzle

                    secret = open_puzzle(cap.key, progress=on_progress)
                else:
                    secret = cap.key
            except Exception as e:
                err = e
            q.put(("done", err, secret))

        def poll():
            finished = False
            err = None
            secret = None
            latest = None
            try:
                while True:
                    item = q.get_nowait()
                    if item[0] == "done":
                        finished = True
                        err = item[1]
                        secret = item[2]
                    elif item[0] == "prog":
                        latest = (item[1], item[2])
            except queue.Empty:
                pass

            if latest is not None:
                done, total = latest
                frac = done / max(total, 1)
                self._draw_cap_timer(None, frac=frac, status=f"{int(frac * 100)}%")

            if finished:
                self._cap_unlocking = False
                if err:
                    messagebox.showerror("Error", str(err))
                    self._on_capsule_select()
                    return
                self._draw_cap_timer(None, frac=1.0, status="LISTO")
                self._finish_capsule_open(cid, secret)
                return

            self.root.after(100, poll)

        threading.Thread(target=work, daemon=True).start()
        self.root.after(100, poll)

    def delete_selected_capsule(self):
        sel = self.cap_tree.selection()
        if not sel:
            return
        cid = int(sel[0])
        cap = next((c for c in getattr(self, "_capsules_cache", []) if c.id == cid), None)
        if not messagebox.askyesno(
            "Confirmar",
            "¿Eliminar la cápsula de la lista?",
        ):
            return
        wipe = False
        if cap and cap.bros_path and os.path.exists(cap.bros_path):
            wipe = messagebox.askyesno(
                "Archivo cifrado",
                f"¿Borrar también el archivo cifrado?\n{cap.bros_path}\n\n"
                "Si no lo borras, el .sbro/.bros queda en disco aunque ya no esté en la lista.",
            )
        self.service.delete_capsule(cid, wipe_bros=wipe)
        self.refresh_capsules()

    def export_selected_capsule(self):
        sel = self.cap_tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona una cápsula para exportar.")
            return
        cid = int(sel[0])
        cap = next((c for c in getattr(self, "_capsules_cache", []) if c.id == cid), None)
        name = (cap.label if cap else "capsula") or "capsula"
        path = filedialog.asksaveasfilename(
            title="Exportar cápsula",
            defaultextension=".sbro",
            filetypes=[("Cápsula CryptoBro", "*.sbro"), ("Todos", "*.*")],
            initialfile=f"{name}.sbro",
        )
        if not path:
            return
        try:
            out = self.service.export_capsule(cid, path)
            messagebox.showinfo("Exportada", f"Cápsula exportada (.sbro):\n{out}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def import_capsule(self):
        path = filedialog.askopenfilename(
            title="Importar cápsula",
            filetypes=[
                ("Cápsula CryptoBro", "*.sbro"),
                ("Cápsula antigua", "*.cap"),
                ("Todos", "*.*"),
            ],
        )
        if not path:
            return
        try:
            cid = self.service.import_capsule(path)
            self.refresh_capsules()
            messagebox.showinfo("Importada", f"Cápsula importada en la bóveda (ID {cid}).")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # --- Messaging Tab ---
    def setup_messages_tab(self):
        """Notas cifradas con grupos/carpetas + export/import."""
        outer = ttk.Frame(self.tab_messages, padding="10")
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        page_header(
            outer,
            "Notas cifradas",
            "Organiza por grupo/carpeta. Exporta .cnote (sigue cifrada; hace falta la contraseña).",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 10))

        frame = ttk.Frame(outer)
        frame.grid(row=1, column=0, sticky="nsew")
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)

        left_panel = ttk.Frame(frame)
        left_panel.grid(row=0, column=0, sticky="nsw", padx=(0, 10))
        left_panel.rowconfigure(1, weight=1)

        right_scroll = ScrollableFrame(frame)
        right_scroll.grid(row=0, column=1, sticky="nsew")
        self._notes_scroll = right_scroll
        self.right_container = right_scroll.interior

        ttk.Label(
            left_panel, text="Grupos / notas", style="Heading.TLabel", font=T.FONT_SUB
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))

        self.msg_tree = ttk.Treeview(
            left_panel,
            columns=("title",),
            show="tree",
            height=16,
            selectmode="browse",
        )
        self.msg_tree.grid(row=1, column=0, sticky="nsew", pady=5)
        self.msg_tree.bind("<<TreeviewSelect>>", self.on_message_select)
        self.msg_tree.tag_configure("folder", foreground=T.FG_MUTED)

        btn_frm_msgs = ttk.Frame(left_panel)
        btn_frm_msgs.grid(row=2, column=0, sticky="ew", pady=5)
        RoundedButton(btn_frm_msgs, text="Actualizar", command=self.refresh_messages_list).pack(
            fill="x", pady=2
        )
        RoundedButton(btn_frm_msgs, text="Exportar", command=self.export_selected_note).pack(
            fill="x", pady=2
        )
        RoundedButton(btn_frm_msgs, text="Importar", command=self.import_note_file).pack(
            fill="x", pady=2
        )
        RoundedButton(btn_frm_msgs, text="Eliminar", command=self.delete_selected_message).pack(
            fill="x", pady=2
        )
        RoundedButton(
            btn_frm_msgs, text="+ Nuevo grupo", command=self.show_new_group_form
        ).pack(fill="x", pady=(10, 2))
        RoundedButton(
            btn_frm_msgs, text="+ Nueva nota", command=lambda: self.show_new_message_form()
        ).pack(fill="x", pady=2)

        self._msg_iid_map = {}
        self._groups_cache = {}
        self.show_new_message_form()
        self.refresh_messages_list()

    @staticmethod
    def _widget_alive(w) -> bool:
        try:
            return w is not None and bool(w.winfo_exists())
        except tk.TclError:
            return False

    def _folder_label(self, folder: str) -> str:
        return folder.strip() if folder and folder.strip() else "Sin grupo"

    def _refresh_folder_combo(self):
        extras = sorted(
            {f for f in self.service.get_message_folders() if f and f.strip()},
            key=str.lower,
        )
        values = ["Sin grupo"] + [f for f in extras if f != "Sin grupo"]
        for attr in ("new_msg_folder_combo", "edit_msg_folder_combo"):
            w = getattr(self, attr, None)
            if self._widget_alive(w):
                try:
                    w["values"] = values
                except tk.TclError:
                    pass
        return values

    def show_new_group_form(self):
        """Formulario para crear un grupo con título y descripción."""
        self.clear_right_panel()
        self.current_viewing_message = None

        ttk.Label(
            self.right_container,
            text="Nuevo grupo",
            style="Page.TLabel",
            font=T.FONT_PAGE,
        ).pack(anchor="w", pady=(4, 12), padx=12)

        form = ttk.Frame(self.right_container)
        form.pack(fill="both", expand=True, padx=20)
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Título", style="Bold.TLabel", font=T.FONT_BOLD).grid(
            row=0, column=0, sticky="w", pady=5
        )
        self.new_group_title = tk.StringVar()
        ttk.Entry(form, textvariable=self.new_group_title).grid(
            row=0, column=1, sticky="ew", pady=5
        )

        ttk.Label(form, text="Descripción", style="Bold.TLabel", font=T.FONT_BOLD).grid(
            row=1, column=0, sticky="nw", pady=5
        )
        desc_box, self.new_group_desc = self._text_box(form, height=6)
        desc_box.grid(row=1, column=1, sticky="nsew", pady=5)
        form.rowconfigure(1, weight=1)

        RoundedButton(form, text="Crear grupo", command=self.save_new_group).grid(
            row=2, column=1, sticky="e", pady=16
        )
        if hasattr(self, "_notes_scroll"):
            self._notes_scroll.scroll_to_top()

    def save_new_group(self):
        title = (self.new_group_title.get() or "").strip()
        desc = self.new_group_desc.get("1.0", tk.END).strip()
        if not title:
            messagebox.showerror("Error", "El grupo necesita un título.")
            return
        if title.lower() == "sin grupo":
            messagebox.showerror("Error", "Ese nombre está reservado.")
            return
        try:
            self.service.create_note_group(title, desc)
            messagebox.showinfo("Listo", f"Grupo «{title}» creado.")
            self.refresh_messages_list()
            self.show_group_view(title)
            fid = f"f:{title}"
            if hasattr(self, "msg_tree") and self.msg_tree.exists(fid):
                self.msg_tree.selection_set(fid)
                self.msg_tree.see(fid)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_group_view(self, folder: str):
        """Panel del grupo: título, descripción y botón + añadir nota."""
        self.clear_right_panel()
        self.current_viewing_message = None
        folder = folder or ""
        label = self._folder_label(folder)
        group = self.service.get_note_group(folder) if folder else None
        desc = (group.description if group else "") or ""

        ttk.Label(
            self.right_container,
            text=label,
            style="Page.TLabel",
            font=T.FONT_PAGE,
        ).pack(anchor="w", pady=(4, 4), padx=12)

        notes_in = [
            m
            for m in (getattr(self, "messages_cache", None) or self.service.get_all_messages())
            if (getattr(m, "folder", "") or "") == folder
        ]
        ttk.Label(
            self.right_container,
            text=f"{len(notes_in)} nota{'s' if len(notes_in) != 1 else ''}",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(0, 10), padx=12)

        form = ttk.Frame(self.right_container)
        form.pack(fill="both", expand=True, padx=20)
        form.columnconfigure(1, weight=1)

        if folder:
            ttk.Label(form, text="Título", style="Bold.TLabel", font=T.FONT_BOLD).grid(
                row=0, column=0, sticky="w", pady=5
            )
            self.edit_group_title = tk.StringVar(value=label)
            ttk.Entry(form, textvariable=self.edit_group_title).grid(
                row=0, column=1, sticky="ew", pady=5
            )

            ttk.Label(form, text="Descripción", style="Bold.TLabel", font=T.FONT_BOLD).grid(
                row=1, column=0, sticky="nw", pady=5
            )
            desc_box, self.edit_group_desc = self._text_box(form, height=5)
            desc_box.grid(row=1, column=1, sticky="nsew", pady=5)
            self.edit_group_desc.insert("1.0", desc)
            form.rowconfigure(1, weight=1)

            self._editing_group_id = group.id if group else None
            self._editing_group_folder = folder

            btns = ttk.Frame(form)
            btns.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 4))
            RoundedButton(
                btns,
                text="+ Añadir nota",
                command=lambda: self.show_new_message_form(prefill_folder=folder),
            ).pack(side="left", padx=(0, 8))
            RoundedButton(btns, text="Guardar grupo", command=self.save_edited_group).pack(
                side="left", padx=4
            )
        else:
            ttk.Label(
                form,
                text="Notas sin grupo asignado.",
                style="Hint.TLabel",
            ).grid(row=0, column=0, columnspan=2, sticky="w", pady=8)
            RoundedButton(
                form,
                text="+ Añadir nota",
                command=lambda: self.show_new_message_form(prefill_folder=""),
            ).grid(row=1, column=0, sticky="w", pady=8)

        if hasattr(self, "_notes_scroll"):
            self._notes_scroll.scroll_to_top()

    def save_edited_group(self):
        folder = getattr(self, "_editing_group_folder", None)
        if folder is None:
            return
        title = (self.edit_group_title.get() or "").strip()
        desc = self.edit_group_desc.get("1.0", tk.END).strip()
        if not title:
            messagebox.showerror("Error", "El grupo necesita un título.")
            return
        if title.lower() == "sin grupo":
            messagebox.showerror("Error", "Ese nombre está reservado.")
            return
        try:
            gid = getattr(self, "_editing_group_id", None)
            if gid is not None:
                self.service.update_note_group(gid, title, desc)
            else:
                existing = self.service.get_note_group(folder)
                if existing:
                    self.service.update_note_group(existing.id, title, desc)
                else:
                    self.service.create_note_group(title, desc)
                    if folder != title:
                        self._rename_notes_folder(folder, title)
            messagebox.showinfo("Listo", "Grupo actualizado.")
            self.refresh_messages_list()
            self.show_group_view(title)
            fid = f"f:{title}"
            if hasattr(self, "msg_tree") and self.msg_tree.exists(fid):
                self.msg_tree.selection_set(fid)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _rename_notes_folder(self, old: str, new: str):
        """Renombra folder en notas sin re-cifrar."""
        for m in self.service.get_all_messages():
            if (m.folder or "") == old:
                self.service.crypto_bro.updateMessage(
                    m.id, m.title, m.content_encrypted, folder=new
                )

    def show_new_message_form(self, prefill_folder: str | None = None):
        """Muestra el formulario para crear un mensaje nuevo."""
        self.clear_right_panel()
        self.current_viewing_message = None

        lbl = ttk.Label(
            self.right_container,
            text="Nueva nota cifrada",
            style="Page.TLabel",
            font=T.FONT_PAGE,
        )
        lbl.pack(anchor="w", pady=(4, 12), padx=12)

        form_frame = ttk.Frame(self.right_container)
        form_frame.pack(fill="both", expand=True, padx=20)
        form_frame.columnconfigure(1, weight=1)

        ttk.Label(form_frame, text="Grupo / carpeta", style="Bold.TLabel", font=T.FONT_BOLD).grid(
            row=0, column=0, sticky="w", pady=5
        )
        default_folder = "Sin grupo"
        if prefill_folder is not None:
            default_folder = self._folder_label(prefill_folder)
        self.new_msg_folder = tk.StringVar(value=default_folder)
        self.new_msg_folder_combo = ttk.Combobox(
            form_frame, textvariable=self.new_msg_folder, values=self._refresh_folder_combo()
        )
        self.new_msg_folder_combo.grid(row=0, column=1, sticky="ew", pady=5)
        ttk.Label(
            form_frame,
            text="Elige un grupo o escribe un nombre nuevo",
            style="Hint.TLabel",
        ).grid(row=1, column=1, sticky="w")

        ttk.Label(form_frame, text="Título", style="Bold.TLabel", font=T.FONT_BOLD).grid(
            row=2, column=0, sticky="w", pady=5
        )
        self.new_msg_title = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.new_msg_title).grid(
            row=2, column=1, sticky="ew", pady=5
        )

        ttk.Label(form_frame, text="Mensaje", style="Bold.TLabel", font=T.FONT_BOLD).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(12, 4)
        )
        content_box, self.new_msg_content = self._text_box(form_frame, height=22)
        content_box.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=5)
        form_frame.rowconfigure(4, weight=1)

        ttk.Label(
            form_frame, text="Contraseña de cifrado", style="Bold.TLabel", font=T.FONT_BOLD
        ).grid(row=5, column=0, sticky="w", pady=5)
        self.new_msg_pass = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.new_msg_pass, show="*").grid(
            row=5, column=1, sticky="ew", pady=5
        )

        RoundedButton(form_frame, text="Guardar nota cifrada", command=self.save_message).grid(
            row=6, column=1, pady=20, sticky="e"
        )
        if hasattr(self, "_notes_scroll"):
            self._notes_scroll.scroll_to_top()

    def show_view_message_form(self, message_obj):
        """Vista bloqueada → Unlock → editor editable."""
        self.clear_right_panel()
        self.current_viewing_message = message_obj
        self._note_unlocked = False
        self._note_password = None

        folder_txt = self._folder_label(getattr(message_obj, "folder", "") or "")
        ttk.Label(
            self.right_container,
            text=message_obj.title,
            style="Page.TLabel",
            font=T.FONT_PAGE,
        ).pack(anchor="w", pady=(4, 2), padx=12)
        ttk.Label(
            self.right_container,
            text=f"Grupo: {folder_txt}",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(0, 10), padx=12)

        form_frame = ttk.Frame(self.right_container)
        form_frame.pack(fill="both", expand=True, padx=20)
        form_frame.columnconfigure(1, weight=1)

        ttk.Label(
            form_frame, text="Contraseña de la nota", style="Bold.TLabel", font=T.FONT_BOLD
        ).grid(row=0, column=0, sticky="w", pady=5)
        self.view_msg_pass = tk.StringVar()
        ent = ttk.Entry(form_frame, textvariable=self.view_msg_pass, show="*")
        ent.grid(row=0, column=1, sticky="ew", pady=5)
        ent.bind("<Return>", lambda e: self.decrypt_and_show_message())
        ent.focus_set()

        RoundedButton(form_frame, text="Desbloquear", command=self.decrypt_and_show_message).grid(
            row=0, column=2, padx=10
        )

        ttk.Label(form_frame, text="Grupo", style="Bold.TLabel", font=T.FONT_BOLD).grid(
            row=1, column=0, sticky="w", pady=5
        )
        self.edit_msg_folder = tk.StringVar(value=folder_txt)
        # readonly mientras bloqueada (disabled rompe el unlock en ttk)
        self.edit_msg_folder_combo = ttk.Combobox(
            form_frame,
            textvariable=self.edit_msg_folder,
            values=self._refresh_folder_combo(),
            state="readonly",
        )
        self.edit_msg_folder_combo.grid(row=1, column=1, columnspan=2, sticky="ew", pady=5)

        ttk.Label(form_frame, text="Título", style="Bold.TLabel", font=T.FONT_BOLD).grid(
            row=2, column=0, sticky="w", pady=5
        )
        self.edit_msg_title = tk.StringVar(value=message_obj.title)
        self.edit_title_entry = ttk.Entry(
            form_frame, textvariable=self.edit_msg_title, state="readonly"
        )
        self.edit_title_entry.grid(row=2, column=1, columnspan=2, sticky="ew", pady=5)

        ttk.Label(form_frame, text="Contenido", style="Bold.TLabel", font=T.FONT_BOLD).grid(
            row=3, column=0, columnspan=3, sticky="w", pady=(12, 4)
        )
        content_box, self.lbl_decrypted_content = self._text_box(form_frame, height=24)
        self.lbl_decrypted_content.configure(state="disabled")
        content_box.grid(row=4, column=0, columnspan=3, sticky="nsew", pady=8)
        form_frame.rowconfigure(4, weight=1)

        btn_row = ttk.Frame(form_frame)
        btn_row.grid(row=5, column=0, columnspan=3, sticky="e", pady=8)
        self.btn_save_note = RoundedButton(
            btn_row, text="Guardar", command=self.save_edited_message, state="disabled"
        )
        self.btn_save_note.pack(side="left", padx=4)
        self.btn_export_note = RoundedButton(
            btn_row, text="Exportar", command=self.export_current_note, state="normal"
        )
        self.btn_export_note.pack(side="left", padx=4)
        self.btn_lock_note = RoundedButton(
            btn_row, text="Bloquear", command=self.lock_note_view, state="disabled"
        )
        self.btn_lock_note.pack(side="left", padx=4)
        if hasattr(self, "_notes_scroll"):
            self._notes_scroll.scroll_to_top()

    def clear_right_panel(self):
        for widget in self.right_container.winfo_children():
            widget.destroy()
        # evita tocar combos destruidos en _refresh_folder_combo
        self.new_msg_folder_combo = None
        self.edit_msg_folder_combo = None
        self.edit_title_entry = None
        self.lbl_decrypted_content = None

    def _normalize_folder_input(self, raw: str) -> str:
        raw = (raw or "").strip()
        if not raw or raw == "Sin grupo":
            return ""
        return raw

    def refresh_messages_list(self):
        if not hasattr(self, "msg_tree"):
            return
        for i in self.msg_tree.get_children():
            self.msg_tree.delete(i)
        self._msg_iid_map = {}
        self.messages_cache = self.service.get_all_messages()
        groups = {g.title: g for g in self.service.get_all_note_groups()}
        self._groups_cache = groups

        by_folder: dict[str, list] = {}
        for msg in self.messages_cache:
            key = getattr(msg, "folder", "") or ""
            by_folder.setdefault(key, []).append(msg)

        # Todos los grupos conocidos (aunque estén vacíos) + Sin grupo si hay notas sueltas
        folder_keys = set(by_folder.keys()) | set(groups.keys())
        if "" not in folder_keys and by_folder.get(""):
            folder_keys.add("")
        # siempre mostrar grupos registrados; Sin grupo solo si hay notas sin carpeta
        if "" in folder_keys and not by_folder.get(""):
            folder_keys.discard("")

        for folder in sorted(folder_keys, key=lambda f: (f == "", (f or "").lower())):
            label = self._folder_label(folder)
            fid = f"f:{folder}"
            self.msg_tree.insert("", "end", iid=fid, text=f"📁 {label}", open=True, tags=("folder",))
            self._msg_iid_map[fid] = None
            for msg in by_folder.get(folder, []):
                nid = f"n:{msg.id}"
                self.msg_tree.insert(fid, "end", iid=nid, text=msg.title)
                self._msg_iid_map[nid] = msg

        self._refresh_folder_combo()

    def on_message_select(self, event=None):
        sel = self.msg_tree.selection() if hasattr(self, "msg_tree") else ()
        if not sel:
            return
        iid = sel[0]
        msg = self._msg_iid_map.get(iid)
        if msg is not None:
            self.show_view_message_form(msg)
            return
        if iid.startswith("f:"):
            self.show_group_view(iid[2:])

    def save_message(self):
        title = self.new_msg_title.get()
        content = self.new_msg_content.get("1.0", tk.END).strip()
        password = self.new_msg_pass.get()
        folder = self._normalize_folder_input(self.new_msg_folder.get())

        if not title or not content or not password:
            messagebox.showerror("Error", "Título, mensaje y contraseña son obligatorios")
            return
        if len(password) < 8:
            messagebox.showerror("Error", "La contraseña debe tener al menos 8 caracteres.")
            return

        try:
            self.service.save_message(title, content, password, folder=folder)
            messagebox.showinfo("Listo", "Nota cifrada y guardada en la bóveda.")
            self.refresh_messages_list()
            if folder:
                self.show_group_view(folder)
                fid = f"f:{folder}"
                if hasattr(self, "msg_tree") and self.msg_tree.exists(fid):
                    self.msg_tree.selection_set(fid)
                    self.msg_tree.see(fid)
            else:
                self.show_new_message_form()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def decrypt_and_show_message(self):
        password = self.view_msg_pass.get()
        if not password:
            messagebox.showerror("Error", "Introduce la contraseña")
            return
        if not self.current_viewing_message:
            return

        try:
            decrypted = self.service.decrypt_message(
                self.current_viewing_message.content_encrypted, password
            )
        except Exception:
            messagebox.showerror(
                "Error", "Falló el descifrado. Contraseña incorrecta o datos corruptos."
            )
            return

        self._note_unlocked = True
        self._note_password = password

        # primero el contenido; el combo no debe tumbar el unlock
        try:
            if self._widget_alive(self.lbl_decrypted_content):
                self.lbl_decrypted_content.config(state="normal")
                self.lbl_decrypted_content.delete("1.0", tk.END)
                self.lbl_decrypted_content.insert("1.0", decrypted)
        except tk.TclError as e:
            messagebox.showerror("Error", f"No se pudo mostrar la nota: {e}")
            return

        try:
            if self._widget_alive(self.edit_title_entry):
                self.edit_title_entry.config(state="normal")
        except tk.TclError:
            pass

        try:
            if self._widget_alive(self.edit_msg_folder_combo):
                # normal = editable (puede crear grupo nuevo)
                self.edit_msg_folder_combo.configure(state="normal")
                self._refresh_folder_combo()
        except tk.TclError:
            pass

        try:
            if self._widget_alive(self.btn_save_note):
                self.btn_save_note.config(state="normal")
            if self._widget_alive(self.btn_lock_note):
                self.btn_lock_note.config(state="normal")
        except tk.TclError:
            pass

    def save_edited_message(self):
        if not self._note_unlocked or not self._note_password:
            return
        title = self.edit_msg_title.get().strip()
        content = self.lbl_decrypted_content.get("1.0", tk.END).rstrip("\n")
        folder = self._normalize_folder_input(self.edit_msg_folder.get())
        if not title:
            messagebox.showerror("Error", "El título es obligatorio")
            return
        try:
            self.service.update_message(
                self.current_viewing_message.id,
                title,
                content,
                self._note_password,
                folder=folder,
            )
            updated = next(
                (
                    m
                    for m in self.service.get_all_messages()
                    if m.id == self.current_viewing_message.id
                ),
                None,
            )
            if updated:
                self.current_viewing_message = updated
            self.refresh_messages_list()
            messagebox.showinfo("Guardado", "Nota cifrada de nuevo y guardada.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def lock_note_view(self):
        if not self.current_viewing_message:
            return
        updated = next(
            (
                m
                for m in self.service.get_all_messages()
                if m.id == self.current_viewing_message.id
            ),
            self.current_viewing_message,
        )
        self.show_view_message_form(updated)

    def _selected_note(self):
        sel = self.msg_tree.selection() if hasattr(self, "msg_tree") else ()
        if not sel:
            return None, None
        iid = sel[0]
        msg = self._msg_iid_map.get(iid)
        if msg is not None:
            return msg, None
        if iid.startswith("f:"):
            return None, iid[2:]  # folder key
        return None, None

    def export_current_note(self):
        if not self.current_viewing_message:
            return
        self._do_export_note(self.current_viewing_message)

    def export_selected_note(self):
        msg, folder = self._selected_note()
        if msg:
            self._do_export_note(msg)
            return
        if folder is not None:
            self._do_export_folder(folder)
            return
        messagebox.showwarning(
            "Aviso", "Selecciona una nota o un grupo para exportar."
        )

    def _do_export_note(self, msg):
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in msg.title)[:40]
        path = filedialog.asksaveasfilename(
            title="Exportar nota",
            defaultextension=".cnote",
            filetypes=[("Nota CryptoBro", "*.cnote")],
            initialfile=f"{safe or 'nota'}.cnote",
        )
        if not path:
            return
        try:
            out = self.service.export_note(msg.id, path)
            messagebox.showinfo(
                "Exportada",
                f"Nota exportada (sigue cifrada):\n{out}\n\n"
                "Para abrirla hace falta la contraseña de la nota.",
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _do_export_folder(self, folder: str):
        label = self._folder_label(folder)
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in label)[:40]
        path = filedialog.asksaveasfilename(
            title="Exportar grupo",
            defaultextension=".cbnotes",
            filetypes=[("Grupo de notas CryptoBro", "*.cbnotes")],
            initialfile=f"{safe or 'grupo'}.cbnotes",
        )
        if not path:
            return
        try:
            out = self.service.export_notes_folder(folder, path)
            messagebox.showinfo(
                "Exportado",
                f"Grupo «{label}» exportado:\n{out}\n\n"
                "Cada nota sigue cifrada con su propia contraseña.",
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def import_note_file(self):
        path = filedialog.askopenfilename(
            title="Importar nota(s)",
            filetypes=[
                ("Notas CryptoBro", "*.cnote *.cbnotes"),
                ("Nota", "*.cnote"),
                ("Grupo", "*.cbnotes"),
                ("Todos", "*.*"),
            ],
        )
        if not path:
            return
        try:
            self.service.import_note(path)
            self.refresh_messages_list()
            messagebox.showinfo("Importada", "Nota(s) importada(s) en la bóveda.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_selected_message(self):
        msg, folder = self._selected_note()
        if msg is not None:
            if messagebox.askyesno("Confirmar", f"¿Eliminar la nota «{msg.title}»?"):
                self.service.delete_message(msg.id)
                self.refresh_messages_list()
                if folder_after := (msg.folder or ""):
                    self.show_group_view(folder_after)
                else:
                    self.show_new_message_form()
            return
        if folder is not None:
            if folder == "":
                messagebox.showinfo("Aviso", "«Sin grupo» no se puede eliminar.")
                return
            label = self._folder_label(folder)
            n = sum(
                1
                for m in (getattr(self, "messages_cache", None) or [])
                if (m.folder or "") == folder
            )
            extra = (
                f"\nLas {n} nota(s) del grupo pasarán a «Sin grupo»."
                if n
                else ""
            )
            if messagebox.askyesno("Confirmar", f"¿Eliminar el grupo «{label}»?{extra}"):
                try:
                    self.service.delete_note_group(folder, move_notes_to_root=True)
                    self.refresh_messages_list()
                    self.show_new_message_form()
                except Exception as e:
                    messagebox.showerror("Error", str(e))
            return
        messagebox.showwarning("Aviso", "Selecciona una nota o un grupo.")
