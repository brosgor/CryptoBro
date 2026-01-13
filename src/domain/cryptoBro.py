
import hashlib
import datetime
from cryptography.fernet import Fernet 
class CryptoBro:
    def __init__(self):
        pass

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
    
    