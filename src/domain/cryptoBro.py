
import base64
import hashlib
import datetime
from cryptography.fernet import Fernet 
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from repository.database import Database
from models.secure_data import SecureData
import os
class CryptoBro:
    def __init__(self):
        self.db = Database('data/secure.db')

    def _deriveKey(self, key:str, salt:bytes=None):
        """Deriva una clave Fernet de 32 bytes desde una contraseña."""
        if salt is None:
            salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key_derived = base64.urlsafe_b64encode(kdf.derive(key.encode()))
        return key_derived.decode(), salt
    
    def generateHash(self, message:str)-> str:
        return hashlib.sha256(message.encode()).hexdigest()
    
    def verifyHash(self, message:str, hash:str)-> bool:
        return self.generateHash(message) == hash
    def timeNow(self)->str:
        date = datetime.datetime.now()
        return date.strftime("%Y-%m-%d %H:%M:%S")

    def generateHashByCurrentTime(self,time:str = None)-> str:
        current_time = time if time is not None else self.timeNow()
        return self.generateHash(message = current_time)
    def generateKey(self)-> str:
        return Fernet.generate_key().decode()
    def encryptMessage(self, message:str, key:str,generated:bool=False)-> str:
        salt_hex = ""
        if not generated:
            key, salt = self._deriveKey(key)
            salt_hex = salt.hex()
        fernet =Fernet(key.encode())
        encrypted_message = fernet.encrypt(message.encode())
        return salt_hex + encrypted_message.decode()

    def decryptMessage(self, encrypted_message:str, key:str, generated:bool=False)-> str:
        if not generated:
            salt_hex = encrypted_message[:32]
            try:
                salt = bytes.fromhex(salt_hex)
            except ValueError:
                # Handle lagacy or invalid format if necessary, or just fail
                raise ValueError("Invalid encrypted message format (missing salt)")
            encrypted_message = encrypted_message[32:]
            key, _ = self._deriveKey(key, salt)

        fernet =Fernet(key.encode())
        decrypted_message = fernet.decrypt(encrypted_message.encode())
        return decrypted_message.decode()

    def encryptFile(self, file_path:str, key:str,generated:bool=False)-> tuple[str, str]:
        salt = b''
        if not generated:
            key, salt = self._deriveKey(key)
        else:
             # Placeholder salt for files encrypted with raw key to maintain structure
             salt = b'\0' * 16

        fernet = Fernet(key.encode())
        with open(file_path, 'rb') as file:
            original = file.read()
        encrypted = fernet.encrypt(original)
        base, ext = os.path.splitext(file_path)
        
        # Use derived key to encrypt extension (generated=True)
        # Since we use the same key, we don't need a separate salt for extension
        extension_encrypted = self.encryptMessage(message=ext,key=key, generated=True)
        
        encrypted_path = base + '.bros'
        with open(encrypted_path, 'wb') as encrypted_file:
            encrypted_file.write(salt)
            encrypted_file.write(encrypted)
        return extension_encrypted, key

    def decryptFile(self, file_path:str, key:str,extension:str=None,generated:bool=False)-> None:
        with open(file_path, 'rb') as encrypted_file:
            file_salt = encrypted_file.read(16)
            encrypted = encrypted_file.read()
            
        if not generated:
            key, _ = self._deriveKey(key, salt=file_salt)
            
        fernet =Fernet(key.encode())
        
        decrypted = fernet.decrypt(encrypted)
        base, ext = os.path.splitext(file_path)
        if extension is not None:
            # Extension was encrypted with the raw derived key (generated=True)
            extension_decrypted = self.decryptMessage(encrypted_message=extension,key=key, generated=True)
        else:
            extension_decrypted = '.gor'
        decrypted_path = base + extension_decrypted
        with open(decrypted_path, 'wb') as decrypted_file:
            decrypted_file.write(decrypted)
        
    def generate_and_store_key(self, hash:str,key:str, extension:str,generated:bool=False)-> str:
        if not generated:
            key, _ = self._deriveKey(key)
        self.db.addItem(hash=hash, key=key, extension=extension)

        return key
    def getItemByHash(self, hash:str)-> SecureData:
        return self.db.getItemByHash(hash)         

    def delete_key_by_id(self, item_id:int)-> None: 
        self.db.deleteItemById(item_id)     
    
    def getAllItems(self)-> list:
        return self.db.getAllItems()
