import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from service.cryptoService import CryptoService
from domain.vault import Vault
from domain.paths import ICON_PNG
from gui.widgets import RoundedButton
from gui import theme as T
from gui.theme import apply_ttk_theme
import os

class CryptoApp:
    """Clase principal de la interfaz gráfica GUI basada en Tkinter."""
    def __init__(self, root, vault: Vault):
        """Inicializa la ventana principal, dimensiones y servicio."""
        self.root = root
        self.root.title("CryptoBro")
        self.root.geometry("900x600")
        self._set_icon()

        self.service = CryptoService(vault)

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

        self.tab_encrypt = ttk.Frame(tabControl)
        self.tab_decrypt = ttk.Frame(tabControl)
        self.tab_capsules = ttk.Frame(tabControl)
        self.tab_messages = ttk.Frame(tabControl)
        self.tab_hash = ttk.Frame(tabControl)
        self.tab_gen = ttk.Frame(tabControl)
        self.tab_keys = ttk.Frame(tabControl)

        tabControl.add(self.tab_encrypt, text="Cifrar")
        tabControl.add(self.tab_decrypt, text="Descifrar")
        tabControl.add(self.tab_capsules, text="Cápsulas")
        tabControl.add(self.tab_messages, text="Notas")
        tabControl.add(self.tab_hash, text="Hash")
        tabControl.add(self.tab_gen, text="Generador")
        tabControl.add(self.tab_keys, text="Claves")

        tabControl.pack(expand=1, fill="both", padx=10, pady=10)

        self.setup_encrypt_tab()
        self.setup_decrypt_tab()
        self.setup_capsules_tab()
        self.setup_messages_tab()
        self.setup_hash_tab()
        self.setup_generator_tab()
        self.setup_keys_tab()

    def setup_encrypt_tab(self):
        """Configura los widgets de la pestaña de encriptación."""
        frame = ttk.Frame(self.tab_encrypt, padding="20")
        frame.pack(fill="both", expand=True)

        frame.columnconfigure(1, weight=1)
        
        # File Selection
        self.enc_file_path = tk.StringVar()
        ttk.Label(frame, text="File to Encrypt:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.enc_file_path).grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        RoundedButton(frame, text="Browse", command=self.browse_encrypt_file).grid(row=0, column=2, padx=5, pady=5)
        
        # Key
        ttk.Label(frame, text="Encryption Key:").grid(row=1, column=0, sticky="w", pady=5)
        self.enc_key = tk.StringVar()
        ttk.Entry(frame, textvariable=self.enc_key, show="*").grid(row=1, column=1, sticky="ew", pady=5, padx=5)
        
        # Store Checkbox
        self.store_key_var = tk.BooleanVar(value=True)
        cb = ttk.Checkbutton(frame, text="Store key in database?", variable=self.store_key_var, command=self.toggle_encrypt_pass_info)
        cb.grid(row=2, column=1, sticky="w", pady=(10, 5), padx=5)

        # Passphrase Info labels
        self.lbl_pass_title = ttk.Label(frame, text="Passphrase Generation:")
        self.lbl_pass_info = ttk.Label(frame, text="A 6-word memorable passphrase will be generated automatically.", wraplength=400)
        
        # Action Button
        self.btn_action = RoundedButton(frame, text="Encrypt", command=self.perform_encryption)
        self.btn_action.grid(row=4, column=1, pady=20)
        
        self.toggle_encrypt_pass_info()

    def toggle_encrypt_pass_info(self):
        if self.store_key_var.get():
            self.lbl_pass_title.grid(row=3, column=0, sticky="w", pady=5)
            self.lbl_pass_info.grid(row=3, column=1, pady=5, sticky="w", padx=5)
            self.btn_action.config(text="Encrypt & Generate")
        else:
            self.lbl_pass_title.grid_remove()
            self.lbl_pass_info.grid_remove()
            self.btn_action.config(text="Encrypt Only")

    def browse_encrypt_file(self):
        filename = filedialog.askopenfilename()
        if filename:
            self.enc_file_path.set(filename)

    def perform_encryption(self):
        file_path = self.enc_file_path.get()
        key = self.enc_key.get()
        store = self.store_key_var.get()
        
        if not file_path or not key:
            messagebox.showerror("Error", "Please select a file and enter a key.")
            return
        if len(key) < 8:
            messagebox.showerror("Error", "Encryption key must be at least 8 characters.")
            return
            
        try:
            extension, derived_key, bros_path = self.service.encryptFile(file_path, key)
            msg = (
                f"Archivo cifrado.\n"
                f"Salida (nombre opaco): {bros_path}\n"
                f"(El nombre original queda dentro del .bros)"
            )
            
            if store:
                while True:
                    passphrase = self.service.generate_mnemonic_passphrase(6)
                    hash_val = self.service.generate_hash(passphrase)
                    if not self.service.getItemByHash(hash_val):
                        break
                
                self.service.generate_and_store_key(hash=hash_val, key=derived_key, extension=extension, generated=True)
                msg += f"\n\nClave guardada en la bóveda.\nPASSPHRASE: {passphrase}"
                
                if messagebox.askyesno(
                    "Guardar passphrase",
                    f"Tu passphrase de recuperación es:\n\n{passphrase}\n\n"
                    "¿Copiar al portapapeles y guardar en un archivo .par?\n\n"
                    "Aviso: .par es texto plano — se guardará junto al .bros opaco.",
                ):
                    self.root.clipboard_clear()
                    self.root.clipboard_append(passphrase)
                    par_path = os.path.splitext(bros_path)[0] + ".par"
                    with open(par_path, "w") as f:
                        f.write(passphrase)
                    msg += f"\nPassphrase copiada y guardada en: {par_path}"
                else:
                    if messagebox.askyesno("Portapapeles", "¿Copiar passphrase al portapapeles?"):
                        self.root.clipboard_clear()
                        self.root.clipboard_append(passphrase)
                        msg += "\nPassphrase copiada al portapapeles."
                    else:
                        msg += "\n(Anota tu passphrase!)"

            if messagebox.askyesno("¿Borrar original?", "Cifrado listo. ¿Borrar el archivo original (plaintext)?"):
                try:
                    size = os.path.getsize(file_path)
                    with open(file_path, "wb") as f:
                        f.write(os.urandom(size))
                    os.remove(file_path)
                    msg += "\nOriginal file securely overwritten and deleted."
                except OSError as e:
                    msg += f"\nCould not delete original: {e}"
            
            messagebox.showinfo("Success", msg)
            self.refresh_keys_list()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def setup_decrypt_tab(self):
        frame = ttk.Frame(self.tab_decrypt, padding="20")
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        self.dec_file_path = tk.StringVar()
        ttk.Label(frame, text="File to Decrypt (.bros):").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.dec_file_path).grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        RoundedButton(frame, text="Browse", command=self.browse_decrypt_file).grid(row=0, column=2, padx=5, pady=5)
        
        self.dec_mode = tk.StringVar(value="manual")
        ttk.Radiobutton(frame, text="Manual Key", variable=self.dec_mode, value="manual", command=self.toggle_dec_inputs).grid(row=1, column=0, sticky="w", pady=5)
        ttk.Radiobutton(frame, text="From Database", variable=self.dec_mode, value="db", command=self.toggle_dec_inputs).grid(row=1, column=1, sticky="w", pady=5)
        
        self.lbl_dec_key = ttk.Label(frame, text="Decryption Key:")
        self.entry_dec_key = ttk.Entry(frame, show="*")
        
        self.lbl_dec_pass = ttk.Label(frame, text="Passphrase or .par File:")
        self.pass_frame = ttk.Frame(frame)
        self.pass_frame.columnconfigure(0, weight=1)

        self.entry_dec_pass = ttk.Entry(self.pass_frame)
        self.entry_dec_pass.pack(side="left", padx=(0, 5), fill="x", expand=True)
        RoundedButton(self.pass_frame, text="Load .par", command=self.load_par_file).pack(side="left")
        
        self.toggle_dec_inputs()
        
        RoundedButton(frame, text="Decrypt", command=self.perform_decryption).grid(row=4, column=1, pady=20)

    def load_par_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Par Files", "*.par"), ("Text Files", "*.txt")])
        if filename:
            try:
                with open(filename, 'r') as f:
                    content = f.read().strip()
                self.entry_dec_pass.delete(0, tk.END)
                self.entry_dec_pass.insert(0, content)
            except Exception as e:
                messagebox.showerror("Error", f"Could not read file: {e}")

    def browse_decrypt_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Bros Files", "*.bros"), ("All Files", "*.*")])
        if filename:
            self.dec_file_path.set(filename)

    def toggle_dec_inputs(self):
        if self.dec_mode.get() == "manual":
            if hasattr(self, 'lbl_dec_pass'):
                self.lbl_dec_pass.grid_remove()
                self.pass_frame.grid_remove()
            if hasattr(self, 'lbl_dec_key'):
                self.lbl_dec_key.grid(row=2, column=0, sticky="w", pady=5)
                self.entry_dec_key.grid(row=2, column=1, sticky="ew", pady=5, padx=5)
        else:
            if hasattr(self, 'lbl_dec_key'):
                self.lbl_dec_key.grid_remove()
                self.entry_dec_key.grid_remove()
            if hasattr(self, 'lbl_dec_pass'):
                self.lbl_dec_pass.grid(row=2, column=0, sticky="w", pady=5)
                self.pass_frame.grid(row=2, column=1, pady=5, sticky="ew", padx=5)

    def perform_decryption(self):
        file_path = self.dec_file_path.get()
        mode = self.dec_mode.get()
        
        if not file_path:
            messagebox.showerror("Error", "Please select a file.")
            return
            
        key = None
        extension = None
        generated = False 
        
        try:
            if mode == 'db':
                passphrase = self.entry_dec_pass.get()
                if not passphrase:
                    messagebox.showerror("Error", "Please enter the passphrase.")
                    return
                hash_val = self.service.generate_hash(passphrase)
                item = self.service.getItemByHash(hash_val)
                
                if item:
                    extension = item.extension
                    key = item.key
                    generated = True
                else:
                    messagebox.showerror("Error", "No key found for this passphrase.")
                    return
            else:
                key = self.entry_dec_key.get()
                if not key:
                    messagebox.showerror("Error", "Please enter the key.")
                    return
                
            out = self.service.decryptFile(file_path, key, extension=extension, generated=generated)
            messagebox.showinfo("Listo", f"Descifrado correctamente:\n{out}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Decryption failed: {str(e)}")


    def setup_hash_tab(self):
        frame = ttk.Frame(self.tab_hash, padding="16")
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Calculadora de hash", font=("DejaVu Sans", 12, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w"
        )
        ttk.Label(
            frame,
            text="Archivo, carpeta (manifiesto recursivo) o texto. "
            "Usa Calcular cuando quieras. MD5/SHA-1 = checksum; SHA-256 = mejor integridad.",
            wraplength=700,
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(2, 12))

        self.hash_mode = tk.StringVar(value="file")
        modes = ttk.Frame(frame)
        modes.grid(row=2, column=0, columnspan=3, sticky="w", pady=(0, 6))
        ttk.Radiobutton(
            modes, text="Archivo", variable=self.hash_mode, value="file", command=self._toggle_hash_mode
        ).pack(side="left", padx=(0, 12))
        ttk.Radiobutton(
            modes, text="Carpeta", variable=self.hash_mode, value="folder", command=self._toggle_hash_mode
        ).pack(side="left", padx=(0, 12))
        ttk.Radiobutton(
            modes, text="Texto", variable=self.hash_mode, value="text", command=self._toggle_hash_mode
        ).pack(side="left")

        self.hash_path = tk.StringVar()
        self.lbl_hash_path = ttk.Label(frame, text="Ruta:")
        self.entry_hash_path = ttk.Entry(frame, textvariable=self.hash_path)
        self.btn_hash_browse = RoundedButton(frame, text="Examinar", command=self._browse_hash_target)

        self.lbl_hash_text = ttk.Label(frame, text="Texto:")
        self.hash_text = tk.Text(
            frame, height=6, bg=T.SURFACE, fg=T.FG, insertbackground=T.FG, highlightbackground=T.BORDER, highlightthickness=1, borderwidth=0
        )

        self.hash_status = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self.hash_status).grid(
            row=4, column=0, columnspan=3, sticky="w", pady=(4, 0)
        )

        RoundedButton(frame, text="Calcular", command=self.compute_hashes).grid(
            row=5, column=1, sticky="e", pady=10
        )

        self.hash_md5 = tk.StringVar()
        self.hash_sha1 = tk.StringVar()
        self.hash_sha256 = tk.StringVar()
        for i, (lab, var) in enumerate(
            [("MD5", self.hash_md5), ("SHA-1", self.hash_sha1), ("SHA-256", self.hash_sha256)],
            start=6,
        ):
            ttk.Label(frame, text=lab + ":").grid(row=i, column=0, sticky="w", pady=4)
            ent = ttk.Entry(frame, textvariable=var)
            ent.grid(row=i, column=1, sticky="ew", padx=4, pady=4)
            RoundedButton(
                frame, text="Copiar", command=lambda v=var: self._copy_hash(v.get())
            ).grid(row=i, column=2, padx=4)

        self._toggle_hash_mode()

    def setup_generator_tab(self):
        frame = ttk.Frame(self.tab_gen, padding="16")
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Generador de contraseñas", font=("DejaVu Sans", 12, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w"
        )
        ttk.Label(
            frame,
            text="CSPRNG (secrets). Contraseña alfanumérica o frase mnemónica de words.json. "
            "Entropía ≈ length × log₂(alfabeto). Objetivo práctico: ≥ 80 bits.",
            wraplength=700,
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(2, 12))

        self.gen_mode = tk.StringVar(value="password")
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

        self.lbl_gen_len = ttk.Label(self.gen_opts, text="Longitud:")
        self.spin_gen_len = ttk.Spinbox(
            self.gen_opts, from_=8, to=128, textvariable=self.gen_length, width=6
        )
        self.chk_lower = ttk.Checkbutton(self.gen_opts, text="a-z", variable=self.gen_lower)
        self.chk_upper = ttk.Checkbutton(self.gen_opts, text="A-Z", variable=self.gen_upper)
        self.chk_digits = ttk.Checkbutton(self.gen_opts, text="0-9", variable=self.gen_digits)
        self.chk_symbols = ttk.Checkbutton(self.gen_opts, text="Símbolos", variable=self.gen_symbols)

        self.lbl_gen_words = ttk.Label(self.gen_opts, text="Palabras:")
        self.spin_gen_words = ttk.Spinbox(
            self.gen_opts, from_=4, to=12, textvariable=self.gen_words, width=6
        )

        RoundedButton(frame, text="Generar", command=self._run_generator).grid(
            row=4, column=1, sticky="e", pady=12
        )

        self.gen_result = tk.StringVar()
        self.gen_entropy = tk.StringVar(value="")
        ttk.Label(frame, text="Resultado:").grid(row=5, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.gen_result).grid(
            row=5, column=1, sticky="ew", padx=4, pady=4
        )
        RoundedButton(frame, text="Copiar", command=lambda: self._copy_hash(self.gen_result.get())).grid(
            row=5, column=2, padx=4
        )
        ttk.Label(frame, textvariable=self.gen_entropy).grid(
            row=6, column=0, columnspan=3, sticky="w", pady=(4, 0)
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

    def compute_hashes(self):
        try:
            mode = self.hash_mode.get()
            self.hash_status.set("Calculando…")
            self.root.update_idletasks()
            if mode == "file":
                path = self.hash_path.get().strip()
                if not path:
                    messagebox.showerror("Error", "Selecciona un archivo")
                    self.hash_status.set("")
                    return
                if not os.path.isfile(path):
                    messagebox.showerror("Error", f"No es un archivo:\n{path}")
                    self.hash_status.set("")
                    return
                result = self.service.hash_file(path)
                self.hash_status.set(f"Archivo: {os.path.basename(path)}")
            elif mode == "folder":
                path = self.hash_path.get().strip()
                if not path:
                    messagebox.showerror("Error", "Selecciona una carpeta")
                    self.hash_status.set("")
                    return
                if not os.path.isdir(path):
                    messagebox.showerror("Error", f"No es una carpeta:\n{path}")
                    self.hash_status.set("")
                    return
                result = self.service.hash_directory(path)
                self.hash_status.set(
                    f"Carpeta: {result['files']} archivo(s) — hash del manifiesto ordenado"
                )
            else:
                text = self.hash_text.get("1.0", tk.END)
                if text.endswith("\n"):
                    text = text[:-1]
                result = self.service.hash_bytes(text.encode("utf-8"))
                self.hash_status.set(f"Texto: {len(text.encode('utf-8'))} bytes")
            self.hash_md5.set(result["md5"])
            self.hash_sha1.set(result["sha1"])
            self.hash_sha256.set(result["sha256"])
        except Exception as e:
            self.hash_status.set("")
            messagebox.showerror("Error", str(e))

    def setup_keys_tab(self):
        frame = ttk.Frame(self.tab_keys, padding="20")
        frame.pack(fill="both", expand=True)

        from domain.paths import get_workspace, cipher_dir, plain_dir

        ttk.Label(
            frame,
            text=f"Bóveda activa: {self.service.vault.name}",
            font=("DejaVu Sans", 11, "bold"),
        ).pack(anchor="w", pady=(0, 4))
        ttk.Label(
            frame,
            text=f"Workspace: {get_workspace()}\n"
            f"Cifrados → {cipher_dir()}\n"
            f"Descifrados → {plain_dir()}",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(0, 8))

        columns = ("ID", "Hash", "Extension")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Hash", text="Hash passphrase")
        self.tree.heading("Extension", text="Extensión")

        self.tree.column("ID", width=50)
        self.tree.column("Hash", width=300)
        self.tree.column("Extension", width=100)

        self.tree.pack(fill="both", expand=True)

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

        vault_btns = ttk.Frame(frame)
        vault_btns.pack(pady=6)
        RoundedButton(
            vault_btns, text="Cambiar clave de bloqueo", command=self.change_lock_password
        ).pack(side="left", padx=4)
        RoundedButton(
            vault_btns, text="Vaciar bóveda", command=self.reset_current_vault
        ).pack(side="left", padx=4)
        RoundedButton(
            vault_btns, text="Eliminar esta bóveda", command=self.delete_current_vault
        ).pack(side="left", padx=4)

        self.refresh_keys_list()

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
            "Eliminar bóveda",
            f"¿Eliminar «{name}» y cerrar?\nNo se pide clave.",
        ):
            return
        try:
            self.service.delete_current_vault()
            messagebox.showinfo("Eliminada", f"Bóveda «{name}» eliminada.")
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def export_vault_backup(self):
        path = filedialog.asksaveasfilename(
            title="Exportar bóveda",
            defaultextension=".gor",
            filetypes=[
                ("Bóveda CryptoBro", "*.gor"),
                ("Backup legacy", "*.cbvault"),
            ],
            initialfile=f"{self.service.vault.name}.gor",
        )
        if not path:
            return
        try:
            out = self.service.export_vault_backup(path)
            messagebox.showinfo(
                "Backup listo",
                f"Exportado a:\n{out}\n\n"
                "Un solo archivo .gor (sigue cifrado). Misma clave de bloqueo para abrirlo.",
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def delete_selected_key(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a key to delete.")
            return
            
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this key?"):
            try:
                item_values = self.tree.item(selected_item, 'values')
                item_id = item_values[0]
                self.service.delete_key_by_id(item_id)
                self.refresh_keys_list()
                messagebox.showinfo("Success", "Key deleted successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete: {e}")

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
            text="Cápsula temporal (puzzle offline)",
            font=("DejaVu Sans", 12, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            frame,
            text="100 % local: la clave se envuelve en un time-lock (squarings). "
            "Al desbloquear, la CPU debe trabajar ≈ la duración elegida. "
            "No usa reloj ni internet. CPU más rápida = abre antes.",
            wraplength=760,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 10))

        body = ttk.Frame(frame)
        body.grid(row=2, column=0, sticky="nsew")
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        form = ttk.Frame(body, padding=8)
        form.grid(row=0, column=0, sticky="nsw")
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Archivo:").grid(row=0, column=0, sticky="w", pady=3)
        self.cap_file = tk.StringVar()
        ttk.Entry(form, textvariable=self.cap_file, width=28).grid(row=0, column=1, sticky="ew", padx=4)
        RoundedButton(form, text="…", padx=10, pady=6, command=self._browse_capsule_file).grid(row=0, column=2)

        ttk.Label(form, text="Etiqueta:").grid(row=1, column=0, sticky="w", pady=3)
        self.cap_label = tk.StringVar()
        ttk.Entry(form, textvariable=self.cap_label).grid(row=1, column=1, columnspan=2, sticky="ew", padx=4)

        ttk.Label(form, text="Trabajo CPU:").grid(row=2, column=0, sticky="nw", pady=6)
        dur = ttk.Frame(form)
        dur.grid(row=2, column=1, columnspan=2, sticky="w")
        self.cap_years = tk.StringVar(value="0")
        self.cap_days = tk.StringVar(value="0")
        self.cap_hours = tk.StringVar(value="0")
        self.cap_mins = tk.StringVar(value="0")
        self.cap_secs = tk.StringVar(value="10")
        for i, (lab, var) in enumerate(
            [
                ("Años", self.cap_years),
                ("Días", self.cap_days),
                ("Horas", self.cap_hours),
                ("Min", self.cap_mins),
                ("Seg", self.cap_secs),
            ]
        ):
            ttk.Label(dur, text=lab).grid(row=0, column=i)
            ttk.Entry(dur, textvariable=var, width=5).grid(row=1, column=i, padx=2)

        self.cap_del_orig = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            form, text="Borrar original tras cifrar", variable=self.cap_del_orig
        ).grid(row=3, column=1, columnspan=2, sticky="w", pady=6)

        RoundedButton(form, text="Crear cápsula", command=self.create_capsule).grid(
            row=4, column=1, sticky="e", pady=10
        )

        right = ttk.Frame(body, padding=8)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)

        cols = ("id", "label", "work", "path")
        self.cap_tree = ttk.Treeview(right, columns=cols, show="headings", height=10)
        self.cap_tree.heading("id", text="ID")
        self.cap_tree.heading("label", text="Etiqueta")
        self.cap_tree.heading("work", text="Trabajo CPU")
        self.cap_tree.heading("path", text="Archivo")
        self.cap_tree.column("id", width=40)
        self.cap_tree.column("label", width=140)
        self.cap_tree.column("work", width=120)
        self.cap_tree.column("path", width=260)
        self.cap_tree.grid(row=0, column=0, sticky="nsew")
        self.cap_tree.bind("<<TreeviewSelect>>", self._on_capsule_select)

        anim = ttk.Frame(right)
        anim.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self.cap_timer_canvas = tk.Canvas(
            anim, width=96, height=96, bg=T.BG, highlightthickness=0
        )
        self.cap_timer_canvas.pack(side="left", padx=(0, 12))
        self.cap_timer_text = tk.StringVar(value="Selecciona una cápsula")
        self.cap_timer_sub = tk.StringVar(value="")
        txt = ttk.Frame(anim)
        txt.pack(side="left", fill="x", expand=True)
        ttk.Label(txt, textvariable=self.cap_timer_text, font=("DejaVu Sans", 16, "bold")).pack(
            anchor="w"
        )
        ttk.Label(txt, textvariable=self.cap_timer_sub, style="Hint.TLabel").pack(anchor="w")
        self._cap_unlock_progress = None  # (done, total) mientras resuelve

        btns = ttk.Frame(right)
        btns.grid(row=2, column=0, sticky="ew", pady=8)
        self.btn_unlock_cap = RoundedButton(
            btns, text="Resolver / Desbloquear", command=self.unlock_selected_capsule, state="disabled"
        )
        self.btn_unlock_cap.pack(side="left", padx=4)
        RoundedButton(btns, text="Actualizar", command=self.refresh_capsules).pack(side="left", padx=4)
        RoundedButton(btns, text="Eliminar", command=self.delete_selected_capsule).pack(side="left", padx=4)

        self._draw_cap_timer(None)
        self.refresh_capsules()

    def _browse_capsule_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.cap_file.set(path)

    def _parse_int(self, var, name):
        try:
            v = int(var.get().strip() or "0")
            if v < 0:
                raise ValueError
            return v
        except ValueError as e:
            raise ValueError(f"{name} inválido") from e

    def _cap_work_label(self, cap) -> str:
        from domain.timelock import is_puzzle
        import json

        if is_puzzle(cap.key):
            try:
                secs = int(json.loads(cap.key).get("secs", 0))
                return self._fmt_duration(secs)
            except Exception:
                return "puzzle"
        return "reloj (legado)"

    @staticmethod
    def _fmt_duration(secs: int) -> str:
        if secs < 60:
            return f"~{secs}s CPU"
        if secs < 3600:
            return f"~{secs // 60}m CPU"
        if secs < 86400:
            return f"~{secs // 3600}h CPU"
        return f"~{secs // 86400}d CPU"

    def create_capsule(self):
        path = self.cap_file.get().strip()
        if not path:
            messagebox.showerror("Error", "Selecciona un archivo")
            return
        try:
            cid, unlock_at, bros, secs = self.service.create_time_capsule(
                file_path=path,
                label=self.cap_label.get(),
                years=self._parse_int(self.cap_years, "Años"),
                days=self._parse_int(self.cap_days, "Días"),
                hours=self._parse_int(self.cap_hours, "Horas"),
                minutes=self._parse_int(self.cap_mins, "Min"),
                seconds=self._parse_int(self.cap_secs, "Seg"),
                delete_original=self.cap_del_orig.get(),
            )
            messagebox.showinfo(
                "Cápsula creada",
                f"ID {cid}\nTrabajo al desbloquear: {self._fmt_duration(secs)}\n\n"
                f"Archivo: {bros}\n\n"
                "Offline. La clave no está en claro: hay que resolver el puzzle con CPU.",
            )
            self.cap_file.set("")
            self.refresh_capsules()
            if self.cap_tree.exists(str(cid)):
                self.cap_tree.selection_set(str(cid))
                self._on_capsule_select()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _draw_cap_timer(self, cap, frac=None, status=None):
        import math

        c = self.cap_timer_canvas
        c.delete("all")
        pad, size = 8, 96
        x0, y0, x1, y1 = pad, pad, size - pad, size - pad
        c.create_oval(x0, y0, x1, y1, outline=T.BORDER, width=8)
        if cap is None and frac is None:
            self.cap_timer_text.set("Selecciona una cápsula")
            self.cap_timer_sub.set("Offline · time-lock puzzle")
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
            self.cap_timer_sub.set("Resolviendo puzzle…")
            return

        c.create_oval(x0 + 12, y0 + 12, x1 - 12, y1 - 12, outline=T.ACCENT, width=3)
        self.cap_timer_text.set(self._cap_work_label(cap))
        self.cap_timer_sub.set(f"{cap.label or f'#{cap.id}'} · pulsa Resolver")

    def refresh_capsules(self):
        if not hasattr(self, "cap_tree"):
            return
        sel = self.cap_tree.selection()
        for i in self.cap_tree.get_children():
            self.cap_tree.delete(i)
        self._capsules_cache = self.service.get_all_capsules()
        for c in self._capsules_cache:
            self.cap_tree.insert(
                "",
                "end",
                iid=str(c.id),
                values=(c.id, c.label, self._cap_work_label(c), c.bros_path),
            )
        if sel and self.cap_tree.exists(sel[0]):
            self.cap_tree.selection_set(sel[0])
            self.cap_tree.focus(sel[0])
        self._on_capsule_select()

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
        self.btn_unlock_cap.config(state="disabled" if unlocking else "normal")
        if not unlocking:
            self._draw_cap_timer(cap)

    def unlock_selected_capsule(self):
        import threading

        sel = self.cap_tree.selection()
        if not sel or getattr(self, "_cap_unlocking", False):
            return
        cid = int(sel[0])
        self._cap_unlocking = True
        self.btn_unlock_cap.config(state="disabled")
        self._draw_cap_timer(None, frac=0.0, status="0%")

        def on_progress(done, total):
            frac = done / max(total, 1)
            self.root.after(
                0,
                lambda f=frac: self._draw_cap_timer(
                    None, frac=f, status=f"{int(f * 100)}%"
                ),
            )

        def work():
            err = None
            try:
                self.service.unlock_capsule(cid, progress=on_progress)
            except Exception as e:
                err = e

            def done():
                self._cap_unlocking = False
                if err:
                    messagebox.showerror("Error", str(err))
                    self._on_capsule_select()
                    return
                self._draw_cap_timer(None, frac=1.0, status="LISTO")
                messagebox.showinfo(
                    "Listo",
                    "Cápsula desbloqueada.\nArchivo restaurado con su nombre original.",
                )
                if messagebox.askyesno("Limpiar", "¿Eliminar esta cápsula de la lista?"):
                    self.service.delete_capsule(cid)
                self.refresh_capsules()

            self.root.after(0, done)

        threading.Thread(target=work, daemon=True).start()

    def delete_selected_capsule(self):
        sel = self.cap_tree.selection()
        if not sel:
            return
        if not messagebox.askyesno(
            "Confirmar",
            "¿Eliminar la cápsula de la bóveda?\n(El .bros en disco no se borra automáticamente.)",
        ):
            return
        self.service.delete_capsule(int(sel[0]))
        self.refresh_capsules()

    # --- Messaging Tab ---
    def setup_messages_tab(self):
        """Setup for the Secure Messages Tab"""
        frame = ttk.Frame(self.tab_messages, padding="10")
        frame.pack(fill="both", expand=True)
        
        # Split into Left (List) and Right (Details)
        left_panel = ttk.Frame(frame)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        
        right_panel = ttk.Frame(frame)
        right_panel.pack(side="left", fill="both", expand=True)
        
        # -- Left Panel: Message List --
        ttk.Label(left_panel, text="Stored Messages").pack(pady=5)
        
        self.msg_listbox = tk.Listbox(left_panel, bg=T.SURFACE, fg=T.FG, selectbackground=T.SELECT, selectforeground=T.SELECT_FG, borderwidth=1, highlightthickness=1, highlightbackground=T.BORDER)
        self.msg_listbox.pack(fill="both", expand=True, pady=5)
        self.msg_listbox.bind('<<ListboxSelect>>', self.on_message_select)
        
        btn_frm_msgs = ttk.Frame(left_panel)
        btn_frm_msgs.pack(fill="x", pady=5)
        RoundedButton(btn_frm_msgs, text="Refresh", command=self.refresh_messages_list).pack(fill="x", pady=2)
        RoundedButton(btn_frm_msgs, text="Delete", command=self.delete_selected_message).pack(fill="x", pady=2)
        RoundedButton(btn_frm_msgs, text="+ New Message", command=self.show_new_message_form).pack(fill="x", pady=(10, 2))

        # -- Right Panel: forms --
        # We will use frames to switch between "New Message" and "View Message"
        self.right_container = right_panel
        self.show_new_message_form() # Default view

    def show_new_message_form(self):
        """Muestra el formulario para crear un mensaje nuevo."""
        self.clear_right_panel()
        
        lbl = ttk.Label(self.right_container, text="Create New Secure Message", font=("DejaVu Sans", 12, "bold"))
        lbl.pack(pady=10)
        
        form_frame = ttk.Frame(self.right_container)
        form_frame.pack(fill="both", expand=True, padx=20)
        form_frame.columnconfigure(1, weight=1)
        
        ttk.Label(form_frame, text="Title:").grid(row=0, column=0, sticky="w", pady=5)
        self.new_msg_title = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.new_msg_title).grid(row=0, column=1, sticky="ew", pady=5)
        
        ttk.Label(form_frame, text="Message:").grid(row=1, column=0, sticky="nw", pady=5)
        self.new_msg_content = tk.Text(form_frame, height=10, bg=T.SURFACE, fg=T.FG, insertbackground=T.FG, highlightbackground=T.BORDER, highlightthickness=1, borderwidth=0)
        self.new_msg_content.grid(row=1, column=1, sticky="ew", pady=5)
        
        ttk.Label(form_frame, text="Encryption Password:").grid(row=2, column=0, sticky="w", pady=5)
        self.new_msg_pass = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.new_msg_pass, show="*").grid(row=2, column=1, sticky="ew", pady=5)
        
        RoundedButton(form_frame, text="Save Encrypted Message", command=self.save_message).grid(row=3, column=1, pady=20, sticky="e")

    def show_view_message_form(self, message_obj):
        """Vista bloqueada → Unlock → editor editable (estilo vault)."""
        self.clear_right_panel()
        self.current_viewing_message = message_obj
        self._note_unlocked = False
        self._note_password = None

        ttk.Label(
            self.right_container,
            text=message_obj.title,
            font=("DejaVu Sans", 12, "bold"),
        ).pack(pady=(10, 4))

        form_frame = ttk.Frame(self.right_container)
        form_frame.pack(fill="both", expand=True, padx=20)
        form_frame.columnconfigure(1, weight=1)

        ttk.Label(form_frame, text="Note password:").grid(row=0, column=0, sticky="w", pady=5)
        self.view_msg_pass = tk.StringVar()
        ent = ttk.Entry(form_frame, textvariable=self.view_msg_pass, show="*")
        ent.grid(row=0, column=1, sticky="ew", pady=5)
        ent.bind("<Return>", lambda e: self.decrypt_and_show_message())
        ent.focus_set()

        RoundedButton(form_frame, text="Unlock", command=self.decrypt_and_show_message).grid(
            row=0, column=2, padx=10
        )

        ttk.Label(form_frame, text="Title:").grid(row=1, column=0, sticky="w", pady=5)
        self.edit_msg_title = tk.StringVar(value=message_obj.title)
        self.edit_title_entry = ttk.Entry(
            form_frame, textvariable=self.edit_msg_title, state="disabled"
        )
        self.edit_title_entry.grid(row=1, column=1, columnspan=2, sticky="ew", pady=5)

        self.lbl_decrypted_content = tk.Text(
            form_frame,
            height=14,
            bg=T.SURFACE,
            fg=T.FG,
            insertbackground=T.FG,
            state="disabled",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=T.BORDER,
            wrap="word",
        )
        self.lbl_decrypted_content.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=12)
        form_frame.rowconfigure(2, weight=1)

        btn_row = ttk.Frame(form_frame)
        btn_row.grid(row=3, column=0, columnspan=3, sticky="e", pady=8)
        self.btn_save_note = RoundedButton(
            btn_row, text="Save", command=self.save_edited_message, state="disabled"
        )
        self.btn_save_note.pack(side="left", padx=4)
        self.btn_lock_note = RoundedButton(
            btn_row, text="Lock", command=self.lock_note_view, state="disabled"
        )
        self.btn_lock_note.pack(side="left", padx=4)

    def clear_right_panel(self):
        for widget in self.right_container.winfo_children():
            widget.destroy()

    def refresh_messages_list(self):
        self.msg_listbox.delete(0, tk.END)
        self.messages_cache = self.service.get_all_messages()
        for msg in self.messages_cache:
            self.msg_listbox.insert(tk.END, msg.title)

    def on_message_select(self, event):
        selection = self.msg_listbox.curselection()
        if selection:
            index = selection[0]
            msg_obj = self.messages_cache[index]
            self.show_view_message_form(msg_obj)

    def save_message(self):
        title = self.new_msg_title.get()
        content = self.new_msg_content.get("1.0", tk.END).strip()
        password = self.new_msg_pass.get()

        if not title or not content or not password:
            messagebox.showerror("Error", "All fields are required")
            return
        if len(password) < 8:
            messagebox.showerror("Error", "Password must be at least 8 characters.")
            return

        try:
            self.service.save_message(title, content, password)
            messagebox.showinfo("Success", "Message encrypted and stored in database.")
            self.refresh_messages_list()
            self.new_msg_title.set("")
            self.new_msg_content.delete("1.0", tk.END)
            self.new_msg_pass.set("")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def decrypt_and_show_message(self):
        password = self.view_msg_pass.get()
        if not password:
            messagebox.showerror("Error", "Enter the password")
            return

        try:
            decrypted = self.service.decrypt_message(
                self.current_viewing_message.content_encrypted, password
            )
        except Exception:
            messagebox.showerror(
                "Error", "Decryption failed. Wrong password OR corrupted data."
            )
            return

        self._note_unlocked = True
        self._note_password = password

        self.edit_title_entry.config(state="normal")
        self.lbl_decrypted_content.config(state="normal")
        self.lbl_decrypted_content.delete("1.0", tk.END)
        self.lbl_decrypted_content.insert("1.0", decrypted)
        self.btn_save_note.config(state="normal")
        self.btn_lock_note.config(state="normal")

    def save_edited_message(self):
        if not getattr(self, "_note_unlocked", False) or not self._note_password:
            return
        title = self.edit_msg_title.get().strip()
        content = self.lbl_decrypted_content.get("1.0", tk.END).rstrip("\n")
        if not title:
            messagebox.showerror("Error", "Title is required")
            return
        try:
            self.service.update_message(
                self.current_viewing_message.id, title, content, self._note_password
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
            messagebox.showinfo("Saved", "Note re-encrypted and saved.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def lock_note_view(self):
        """Quita el plaintext de pantalla."""
        if not self.current_viewing_message:
            return
        self._note_password = None
        self._note_unlocked = False
        # refresh ciphertext before re-showing locked view
        updated = next(
            (
                m
                for m in self.service.get_all_messages()
                if m.id == self.current_viewing_message.id
            ),
            self.current_viewing_message,
        )
        self.show_view_message_form(updated)

    def delete_selected_message(self):
        selection = self.msg_listbox.curselection()
        if not selection:
            return

        if messagebox.askyesno("Confirm", "Delete this message?"):
            index = selection[0]
            msg_obj = self.messages_cache[index]
            self.service.delete_message(msg_obj.id)
            self.refresh_messages_list()
            self.show_new_message_form()
