from domain.cryptoBro import CryptoBro
class CryptoService:
    def __init__(self):
        self.crypto_bro = CryptoBro()
    def generate_hash(self, message: str) -> str:
        return self.crypto_bro.generateHash(message)
    def verify_hash(self, message: str, hash: str) -> bool:
        return self.crypto_bro.verifyHash(message, hash)
    def generate_key(self) -> str:
        return self.crypto_bro.generateKey()
    def encrypt_message(self, message: str, key: str) -> str:
        return self.crypto_bro.encryptMessage(message, key)
    def decrypt_message(self, encrypted_message: str, key: str) -> str:
        return self.crypto_bro.decryptMessage(encrypted_message, key)   
    def encryptFile(self, file_path: str, key: str) -> str:
        return self.crypto_bro.encryptFile(file_path, key)
    def decryptFile(self, file_path: str, key: str,extension:str) -> None:
        self.crypto_bro.decryptFile(file_path, key,extension=extension)
    def generate_and_store_key(self, hash: str,key:str, extension: str) -> str:
        return self.crypto_bro.generate_and_store_key(hash,key, extension)
    def getItemByHash(self, hash: str) -> tuple:
        return self.crypto_bro.getItemByHash(hash)         
    def delete_key_by_id(self, item_id: int) -> None: 
        self.crypto_bro.delete_key_by_id(item_id)     
    def getAllItems(self) -> list:
        return self.crypto_bro.getAllItems()
