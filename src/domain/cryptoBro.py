
import hashlib
import datetime
from cryptography.fernet import Fernet 
from repository.database import Database
import os
class CryptoBro:
    def __init__(self):
        self.db = Database('data/secure.db')

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
    def encryptMessage(self, message:str, key:str)-> str:
        fernet =Fernet(key.encode())
        encrypted_message = fernet.encrypt(message.encode())
        return encrypted_message.decode()
    def decryptMessage(self, encrypted_message:str, key:str)-> str:
        fernet =Fernet(key.encode())
        decrypted_message = fernet.decrypt(encrypted_message.encode())
        return decrypted_message.decode()
    def encryptFile(self, file_path:str, key:str)-> str:
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
    def decryptFile(self, file_path:str, key:str,extension:str)-> None:
        fernet =Fernet(key.encode())
        with open(file_path, 'rb') as encrypted_file:
            encrypted = encrypted_file.read()
        decrypted = fernet.decrypt(encrypted)
        base, ext = os.path.splitext(file_path)
        extension_decrypted = self.decryptMessage(message=extension,key=key)
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
