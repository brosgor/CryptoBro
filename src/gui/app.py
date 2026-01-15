import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from service.cryptoService import CryptoService
import uuid
import os

class CryptoApp:
    """Clase principal de la interfaz gráfica GUI basada en Tkinter."""
    def __init__(self, root):
        """Inicializa la ventana principal, dimensiones y servicio."""
        self.root = root
        self.root.title("CryptoBro GUI")
        self.root.geometry("900x600")
        
        self.service = CryptoService()
        
        self.apply_theme()
        self.create_widgets()
        
    def apply_theme(self):
        """Aplica un tema oscuro estilo Proton VPN."""
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except:
            pass # Fallback if clam not available

        # Colors
        bg_color = "#1d1d20"         # Dark background
        fg_color = "#ffffff"         # White text
        accent_color = "#6d4aff"     # Proton Purple
        secondary_bg = "#2e2e33"     # Slightly lighter background
        entry_bg = "#38383d"
        
        self.root.configure(background=bg_color)

        # General configurations
        style.configure(".", 
            background=bg_color, 
            foreground=fg_color, 
            fieldbackground=entry_bg,
            font=("Segoe UI", 10)
        )
        
        # TFrame
        style.configure("TFrame", background=bg_color)
        style.configure("TLabelframe", background=bg_color, foreground=fg_color)
        style.configure("TLabelframe.Label", background=bg_color, foreground=fg_color)
        
        # Notebook (Tabs)
        style.configure("TNotebook", background=bg_color, borderwidth=0)
        style.configure("TNotebook.Tab", 
            background=secondary_bg, 
            foreground=fg_color, 
            padding=[10, 5],
            font=("Segoe UI", 10, "bold")
        )
        style.map("TNotebook.Tab", 
            background=[("selected", accent_color)],
            foreground=[("selected", fg_color)]
        )

        # Buttons
        style.configure("TButton", 
            background=accent_color, 
            foreground=fg_color, 
            borderwidth=0, 
            focuscolor="none", # remove focus dashed line
            padding=[10, 5]
        )
        style.map("TButton", 
            background=[("active", "#5835e0"), ("pressed", "#4522cc")],
            relief=[("pressed", "flat")]
        )
        
        # Labels
        style.configure("TLabel", background=bg_color, foreground=fg_color)
        
        # Entry
        style.configure("TEntry", 
            fieldbackground=entry_bg, 
            foreground=fg_color,
            insertcolor=fg_color,
            borderwidth=0
        )
        
        # Treeview
        style.configure("Treeview", 
            background=secondary_bg, 
            foreground=fg_color, 
            fieldbackground=secondary_bg,
            borderwidth=0
        )
        style.configure("Treeview.Heading", 
            background=entry_bg, 
            foreground=fg_color, 
            font=("Segoe UI", 10, "bold"),
            borderwidth=0
        )
        style.map("Treeview", 
            background=[("selected", accent_color)], 
            foreground=[("selected", fg_color)]
        )

        # Checkbutton & Radiobutton
        style.configure("TCheckbutton", background=bg_color, foreground=fg_color, focuscolor=bg_color)
        style.configure("TRadiobutton", background=bg_color, foreground=fg_color, focuscolor=bg_color)
        style.map("TCheckbutton", background=[("active", bg_color)])
        style.map("TRadiobutton", background=[("active", bg_color)])

    def create_widgets(self):
        """Crea y organiza las pestañas principales de la aplicación."""
        # Tab Control
        tabControl = ttk.Notebook(self.root)
        
        self.tab_encrypt = ttk.Frame(tabControl)
        self.tab_decrypt = ttk.Frame(tabControl)
        self.tab_keys = ttk.Frame(tabControl)
        self.tab_messages = ttk.Frame(tabControl) # New Tab
        
        tabControl.add(self.tab_encrypt, text='Encrypt File')
        tabControl.add(self.tab_decrypt, text='Decrypt File')
        tabControl.add(self.tab_messages, text='Secure Messages')
        tabControl.add(self.tab_keys, text='Stored Keys')
        
        tabControl.pack(expand=1, fill="both", padx=10, pady=10)
        
        self.setup_encrypt_tab()
        self.setup_decrypt_tab()
        self.setup_messages_tab()
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
        ttk.Button(frame, text="Browse", command=self.browse_encrypt_file).grid(row=0, column=2, padx=5, pady=5)
        
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
        self.lbl_pass_info = ttk.Label(frame, text="A unique memorable passphrase will be generated automatically.", wraplength=400)
        
        # Action Button
        self.btn_action = ttk.Button(frame, text="Encrypt", command=self.perform_encryption)
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
            
        try:
            extension, derived_key = self.service.encryptFile(file_path, key)
            msg = f"File encrypted successfully! Extension: {extension}"
            
            if store:
                while True:
                    passphrase = self.service.generate_mnemonic_passphrase(3)
                    hash_val = self.service.generate_hash(passphrase)
                    if not self.service.getItemByHash(hash_val):
                        break
                
                self.service.generate_and_store_key(hash=hash_val, key=derived_key, extension=extension, generated=True)
                msg += f"\n\nKey stored securely.\nYOUR PASSPHRASE IS: {passphrase}"
                
                if messagebox.askyesno("Save Passphrase", f"Your recovery passphrase is:\n\n{passphrase}\n\nDo you want to save this to a '.par' file?"):
                    base_path = os.path.splitext(file_path)[0]
                    par_path = base_path + ".par"
                    with open(par_path, 'w') as f:
                        f.write(passphrase)
                    msg += f"\nPassphrase saved to: {par_path}"
                else:
                    msg += "\n(Please write down your passphrase!)"
            
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
        ttk.Button(frame, text="Browse", command=self.browse_decrypt_file).grid(row=0, column=2, padx=5, pady=5)
        
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
        ttk.Button(self.pass_frame, text="Load .par", command=self.load_par_file).pack(side="left")
        
        self.toggle_dec_inputs()
        
        ttk.Button(frame, text="Decrypt", command=self.perform_decryption).grid(row=4, column=1, pady=20)

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
                
            self.service.decryptFile(file_path, key, extension=extension, generated=generated)
            messagebox.showinfo("Success", "File decrypted successfully.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Decryption failed: {str(e)}")

    def setup_keys_tab(self):
        frame = ttk.Frame(self.tab_keys, padding="20")
        frame.pack(fill="both", expand=True)
        
        columns = ('ID', 'Hash', 'Extension')
        self.tree = ttk.Treeview(frame, columns=columns, show='headings')
        self.tree.heading('ID', text='ID')
        self.tree.heading('Hash', text='Passphrase Hash')
        self.tree.heading('Extension', text='Extension')
        
        self.tree.column('ID', width=50)
        self.tree.column('Hash', width=300)
        self.tree.column('Extension', width=100)
        
        self.tree.pack(fill="both", expand=True)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_keys_list).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_selected_key).pack(side="left", padx=5)
        
        self.refresh_keys_list()
    
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
        
        self.msg_listbox = tk.Listbox(left_panel, bg="#2e2e33", fg="#ffffff", selectbackground="#6d4aff", borderwidth=0)
        self.msg_listbox.pack(fill="both", expand=True, pady=5)
        self.msg_listbox.bind('<<ListboxSelect>>', self.on_message_select)
        
        btn_frm_msgs = ttk.Frame(left_panel)
        btn_frm_msgs.pack(fill="x", pady=5)
        ttk.Button(btn_frm_msgs, text="Refresh", command=self.refresh_messages_list).pack(fill="x", pady=2)
        ttk.Button(btn_frm_msgs, text="Delete", command=self.delete_selected_message).pack(fill="x", pady=2)
        ttk.Button(btn_frm_msgs, text="+ New Message", command=self.show_new_message_form).pack(fill="x", pady=(10, 2))

        # -- Right Panel: forms --
        # We will use frames to switch between "New Message" and "View Message"
        self.right_container = right_panel
        self.show_new_message_form() # Default view

    def show_new_message_form(self):
        """Muestra el formulario para crear un mensaje nuevo."""
        self.clear_right_panel()
        
        lbl = ttk.Label(self.right_container, text="Create New Secure Message", font=("Segoe UI", 12, "bold"))
        lbl.pack(pady=10)
        
        form_frame = ttk.Frame(self.right_container)
        form_frame.pack(fill="both", expand=True, padx=20)
        form_frame.columnconfigure(1, weight=1)
        
        ttk.Label(form_frame, text="Title:").grid(row=0, column=0, sticky="w", pady=5)
        self.new_msg_title = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.new_msg_title).grid(row=0, column=1, sticky="ew", pady=5)
        
        ttk.Label(form_frame, text="Message:").grid(row=1, column=0, sticky="nw", pady=5)
        self.new_msg_content = tk.Text(form_frame, height=10, bg="#38383d", fg="white", insertbackground="white", borderwidth=0)
        self.new_msg_content.grid(row=1, column=1, sticky="ew", pady=5)
        
        ttk.Label(form_frame, text="Encryption Password:").grid(row=2, column=0, sticky="w", pady=5)
        self.new_msg_pass = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.new_msg_pass, show="*").grid(row=2, column=1, sticky="ew", pady=5)
        
        ttk.Button(form_frame, text="Save Encrypted Message", command=self.save_message).grid(row=3, column=1, pady=20, sticky="e")

    def show_view_message_form(self, message_obj):
        """Muestra el formulario para desencriptar y ver un mensaje."""
        self.clear_right_panel()
        self.current_viewing_message = message_obj
        
        lbl = ttk.Label(self.right_container, text=f"View Message: {message_obj.title}", font=("Segoe UI", 12, "bold"))
        lbl.pack(pady=10)
        
        form_frame = ttk.Frame(self.right_container)
        form_frame.pack(fill="both", expand=True, padx=20)
        form_frame.columnconfigure(1, weight=1)
        
        ttk.Label(form_frame, text="Enter Password to Decrypt:").grid(row=0, column=0, sticky="w", pady=5)
        self.view_msg_pass = tk.StringVar()
        ent = ttk.Entry(form_frame, textvariable=self.view_msg_pass, show="*")
        ent.grid(row=0, column=1, sticky="ew", pady=5)
        ent.bind('<Return>', lambda e: self.decrypt_and_show_message())
        
        ttk.Button(form_frame, text="Decrypt", command=self.decrypt_and_show_message).grid(row=0, column=2, padx=10)
        
        self.lbl_decrypted_content = tk.Text(form_frame, height=15, bg="#2e2e33", fg="#aaafff", state="disabled", borderwidth=0)
        self.lbl_decrypted_content.grid(row=1, column=0, columnspan=3, sticky="ew", pady=20)

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
            # content is encrypted
            encrypted_content = self.current_viewing_message.content_encrypted
            decrypted = self.service.decrypt_message(encrypted_content, password)
            
            self.lbl_decrypted_content.config(state="normal")
            self.lbl_decrypted_content.delete("1.0", tk.END)
            self.lbl_decrypted_content.insert("1.0", decrypted)
            self.lbl_decrypted_content.config(state="disabled")
        except Exception:
            messagebox.showerror("Error", "Decryption failed. Wrong password OR corrupted data.")

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