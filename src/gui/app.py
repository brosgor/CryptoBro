import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from service.cryptoService import CryptoService

class CryptoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CryptoBro GUI")
        self.root.geometry("600x450")
        
        self.service = CryptoService()
        
        self.create_widgets()
        
    def create_widgets(self):
        # Tab Control
        tabControl = ttk.Notebook(self.root)
        
        self.tab_encrypt = ttk.Frame(tabControl)
        self.tab_decrypt = ttk.Frame(tabControl)
        self.tab_keys = ttk.Frame(tabControl)
        
        tabControl.add(self.tab_encrypt, text='Encrypt File')
        tabControl.add(self.tab_decrypt, text='Decrypt File')
        tabControl.add(self.tab_keys, text='Stored Keys')
        
        tabControl.pack(expand=1, fill="both")
        
        self.setup_encrypt_tab()
        self.setup_decrypt_tab()
        self.setup_keys_tab()

    def setup_encrypt_tab(self):
        frame = ttk.Frame(self.tab_encrypt, padding="20")
        frame.pack(fill="both", expand=True)
        
        # File Selection
        self.enc_file_path = tk.StringVar()
        ttk.Label(frame, text="File to Encrypt:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.enc_file_path, width=40).grid(row=0, column=1, pady=5)
        ttk.Button(frame, text="Browse", command=self.browse_encrypt_file).grid(row=0, column=2, padx=5, pady=5)
        
        # Key
        ttk.Label(frame, text="Encryption Key:").grid(row=1, column=0, sticky="w", pady=5)
        self.enc_key = tk.StringVar()
        ttk.Entry(frame, textvariable=self.enc_key, show="*", width=40).grid(row=1, column=1, pady=5)
        
        # Passphrase (for checking hash later)
        ttk.Label(frame, text="Passphrase (for storage):").grid(row=2, column=0, sticky="w", pady=5)
        self.enc_passphrase = tk.StringVar()
        ttk.Entry(frame, textvariable=self.enc_passphrase, width=40).grid(row=2, column=1, pady=5)
        
        # Store Checkbox
        self.store_key_var = tk.BooleanVar()
        ttk.Checkbutton(frame, text="Store key in database?", variable=self.store_key_var).grid(row=3, column=1, sticky="w", pady=5)
        
        # Action Button
        ttk.Button(frame, text="Encrypt", command=self.perform_encryption).grid(row=4, column=1, pady=20)

    def browse_encrypt_file(self):
        filename = filedialog.askopenfilename()
        if filename:
            self.enc_file_path.set(filename)

    def perform_encryption(self):
        file_path = self.enc_file_path.get()
        key = self.enc_key.get()
        passphrase = self.enc_passphrase.get()
        store = self.store_key_var.get()
        
        if not file_path or not key:
            messagebox.showerror("Error", "Please select a file and enter a key.")
            return
            
        try:
            extension, derived_key = self.service.encryptFile(file_path, key)
            msg = f"File encrypted successfully! Extension: {extension}"
            
            if store:
                if not passphrase:
                    messagebox.showwarning("Warning", "Passphrase required to store key.")
                else:
                    hash_val = self.service.generate_hash(passphrase)
                    self.service.generate_and_store_key(hash=hash_val, key=derived_key, extension=extension, generated=True)
                    msg += f"\nKey stored with hash: {hash_val}"
            
            messagebox.showinfo("Success", msg)
            self.refresh_keys_list()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def setup_decrypt_tab(self):
        frame = ttk.Frame(self.tab_decrypt, padding="20")
        frame.pack(fill="both", expand=True)
        
        # File Selection
        self.dec_file_path = tk.StringVar()
        ttk.Label(frame, text="File to Decrypt (.bros):").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.dec_file_path, width=40).grid(row=0, column=1, pady=5)
        ttk.Button(frame, text="Browse", command=self.browse_decrypt_file).grid(row=0, column=2, padx=5, pady=5)
        
        # Mode Selection
        self.dec_mode = tk.StringVar(value="manual")
        ttk.Radiobutton(frame, text="Manual Key", variable=self.dec_mode, value="manual", command=self.toggle_dec_inputs).grid(row=1, column=0, sticky="w", pady=5)
        ttk.Radiobutton(frame, text="From Database", variable=self.dec_mode, value="db", command=self.toggle_dec_inputs).grid(row=1, column=1, sticky="w", pady=5)
        
        # Manual Input
        self.lbl_dec_key = ttk.Label(frame, text="Decryption Key:")
        self.lbl_dec_key.grid(row=2, column=0, sticky="w", pady=5)
        self.entry_dec_key = ttk.Entry(frame, show="*", width=40)
        self.entry_dec_key.grid(row=2, column=1, pady=5)
        
        # DB Input
        self.lbl_dec_pass = ttk.Label(frame, text="Passphrase:")
        self.entry_dec_pass = ttk.Entry(frame, width=40)
        # Initially hidden/shown based on default
        self.toggle_dec_inputs()
        
        # Action Button
        ttk.Button(frame, text="Decrypt", command=self.perform_decryption).grid(row=4, column=1, pady=20)

    def browse_decrypt_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Bros Files", "*.bros"), ("All Files", "*.*")])
        if filename:
            self.dec_file_path.set(filename)

    def toggle_dec_inputs(self):
        if self.dec_mode.get() == "manual":
            self.lbl_dec_pass.grid_remove()
            self.entry_dec_pass.grid_remove()
            self.lbl_dec_key.grid(row=2, column=0, sticky="w", pady=5)
            self.entry_dec_key.grid(row=2, column=1, pady=5)
        else:
            self.lbl_dec_key.grid_remove()
            self.entry_dec_key.grid_remove()
            self.lbl_dec_pass.grid(row=2, column=0, sticky="w", pady=5)
            self.entry_dec_pass.grid(row=2, column=1, pady=5)

    def perform_decryption(self):
        file_path = self.dec_file_path.get()
        mode = self.dec_mode.get()
        
        if not file_path:
            messagebox.showerror("Error", "Please select a file.")
            return
            
        key = None
        extension = None
        generated = False # Default unless from DB
        
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
                # Manual decryption extension handling is tricky if not stored. 
                # The service will default to .gor if extension is None
                
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
        
        ttk.Button(frame, text="Refresh", command=self.refresh_keys_list).pack(pady=10)
        self.refresh_keys_list()

    def refresh_keys_list(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        items = self.service.getAllItems()
        for item in items:
            self.tree.insert('', 'end', values=(item.id, item.hash, item.extension))
