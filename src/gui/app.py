import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from service.cryptoService import CryptoService
import uuid
import os

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

        # Configure grid responsiveness
        frame.columnconfigure(1, weight=1)
        
        # File Selection
        self.enc_file_path = tk.StringVar()
        ttk.Label(frame, text="File to Encrypt:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.enc_file_path).grid(row=0, column=1, sticky="ew", pady=5)
        ttk.Button(frame, text="Browse", command=self.browse_encrypt_file).grid(row=0, column=2, padx=5, pady=5)
        
        # Key
        ttk.Label(frame, text="Encryption Key:").grid(row=1, column=0, sticky="w", pady=5)
        self.enc_key = tk.StringVar()
        ttk.Entry(frame, textvariable=self.enc_key, show="*").grid(row=1, column=1, sticky="ew", pady=5)
        
        # Store Checkbox (Moved up)
        self.store_key_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Store key in database?", variable=self.store_key_var, command=self.toggle_encrypt_pass_info).grid(row=2, column=1, sticky="w", pady=(10, 5))

        # Passphrase Info labels (Hidden/Shown dynamically)
        self.lbl_pass_title = ttk.Label(frame, text="Passphrase Generation:")
        self.lbl_pass_info = ttk.Label(frame, text="A unique memorable passphrase will be generated automatically.")
        
        # Action Button
        self.btn_action = ttk.Button(frame, text="Encrypt", command=self.perform_encryption)
        self.btn_action.grid(row=4, column=1, pady=20)
        
        # Initialize state
        self.toggle_encrypt_pass_info()

    def toggle_encrypt_pass_info(self):
        if self.store_key_var.get():
            self.lbl_pass_title.grid(row=3, column=0, sticky="w", pady=5)
            self.lbl_pass_info.grid(row=3, column=1, pady=5, sticky="w")
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
                # Generate unique mnemonic passphrase
                while True:
                    passphrase = self.service.generate_mnemonic_passphrase(3)
                    hash_val = self.service.generate_hash(passphrase)
                    if not self.service.getItemByHash(hash_val):
                        break
                
                # Store in DB
                self.service.generate_and_store_key(hash=hash_val, key=derived_key, extension=extension, generated=True)
                
                msg += f"\n\nKey stored securely.\nYOUR PASSPHRASE IS: {passphrase}"
                
                # Ask if user wants to save .par file
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
        
        # Configure grid responsiveness
        frame.columnconfigure(1, weight=1)

        # File Selection
        self.dec_file_path = tk.StringVar()
        ttk.Label(frame, text="File to Decrypt (.bros):").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.dec_file_path).grid(row=0, column=1, sticky="ew", pady=5)
        ttk.Button(frame, text="Browse", command=self.browse_decrypt_file).grid(row=0, column=2, padx=5, pady=5)
        
        # Mode Selection
        self.dec_mode = tk.StringVar(value="manual")
        ttk.Radiobutton(frame, text="Manual Key", variable=self.dec_mode, value="manual", command=self.toggle_dec_inputs).grid(row=1, column=0, sticky="w", pady=5)
        ttk.Radiobutton(frame, text="From Database", variable=self.dec_mode, value="db", command=self.toggle_dec_inputs).grid(row=1, column=1, sticky="w", pady=5)
        
        # Manual Input Widgets
        self.lbl_dec_key = ttk.Label(frame, text="Decryption Key:")
        self.entry_dec_key = ttk.Entry(frame, show="*")
        
        # DB Input Widgets
        self.lbl_dec_pass = ttk.Label(frame, text="Passphrase or .par File:")
        self.pass_frame = ttk.Frame(frame)
        self.pass_frame.columnconfigure(0, weight=1) # Ensure inner frame expands

        self.entry_dec_pass = ttk.Entry(self.pass_frame)
        self.entry_dec_pass.pack(side="left", padx=(0, 5), fill="x", expand=True)
        ttk.Button(self.pass_frame, text="Load .par", command=self.load_par_file).pack(side="left")
        
        # Initially apply visibility state
        self.toggle_dec_inputs()
        
        # Action Button
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
            # Hide DB widgets
            if hasattr(self, 'lbl_dec_pass'):
                self.lbl_dec_pass.grid_remove()
                self.pass_frame.grid_remove()
            
            # Show Manual widgets
            if hasattr(self, 'lbl_dec_key'):
                self.lbl_dec_key.grid(row=2, column=0, sticky="w", pady=5)
                self.entry_dec_key.grid(row=2, column=1, sticky="ew", pady=5)
        else:
            # Hide Manual widgets
            if hasattr(self, 'lbl_dec_key'):
                self.lbl_dec_key.grid_remove()
                self.entry_dec_key.grid_remove()
            
            # Show DB widgets
            if hasattr(self, 'lbl_dec_pass'):
                self.lbl_dec_pass.grid(row=2, column=0, sticky="w", pady=5)
                self.pass_frame.grid(row=2, column=1, pady=5, sticky="ew")


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
            
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this key? This action cannot be undone."):
            try:
                item_values = self.tree.item(selected_item, 'values')
                item_id = item_values[0] # ID is first column
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
