from ..domain.cryptoBro import CryptoBro
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
