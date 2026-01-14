
import base64
import hashlib
import datetime
from cryptography.fernet import Fernet 
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from repository.database import Database
import os
class CryptoBro:
    def __init__(self):
        self.db = Database('data/secure.db')
        self._SALT = b"SALTFIJOPORELMOMENTO"

    def _deriveKey(self, key:str):
        """Deriva una clave Fernet de 32 bytes desde una contraseña."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._SALT,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(key.encode()))
        return key.decode()
    
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
        if not generated:
            key = self._deriveKey(key)
        fernet =Fernet(key.encode())
        encrypted_message = fernet.encrypt(message.encode())
        return encrypted_message.decode()
    def decryptMessage(self, encrypted_message:str, key:str, generated:bool=False)-> str:
        if not generated:
            key = self._deriveKey(key)

        fernet =Fernet(key.encode())
        decrypted_message = fernet.decrypt(encrypted_message.encode())
        return decrypted_message.decode()
    def encryptFile(self, file_path:str, key:str,generated:bool=False)-> str:
        if not generated:
            key = self._deriveKey(key)

        fernet = Fernet(key.encode())
        with open(file_path, 'rb') as file:
            original = file.read()
        encrypted = fernet.encrypt(original)
        base, ext = os.path.splitext(file_path)
        extension_encrypted = self.encryptMessage(message=ext,key=key)
        encrypted_path = base + '.bros'
        with open(encrypted_path, 'wb') as encrypted_file:
            encrypted_file.write(encrypted)
        return extension_encrypted
    def decryptFile(self, file_path:str, key:str,extension:str=None,generated:bool=False)-> None:
        if not generated:
            key = self._deriveKey(key)
        fernet =Fernet(key.encode())
        with open(file_path, 'rb') as encrypted_file:
            encrypted = encrypted_file.read()
        decrypted = fernet.decrypt(encrypted)
        base, ext = os.path.splitext(file_path)
        if extension is not None:
            extension_decrypted = self.decryptMessage(encrypted_message=extension,key=key)
        else:
            extension_decrypted = '.decrypted'
        decrypted_path = base + extension_decrypted
        with open(decrypted_path, 'wb') as decrypted_file:
            decrypted_file.write(decrypted)
        
    def generate_and_store_key(self, hash:str,key:str, extension:str)-> str:
        self.db.addItem(hash=hash, key=key, extension=extension)
        return key
    def getItemByHash(self, hash:str)-> tuple:
        return self.db.getItemByHash(hash)         

    def delete_key_by_id(self, item_id:int)-> None: 
        self.db.deleteItemById(item_id)     
    
    def getAllItems(self)-> list:
        return self.db.getAllItems()
