from domain.cryptoBro import CryptoBro
from models.secure_data import SecureData
import json
import random
import os

class CryptoService:
    """
    Capa de servicio que actúa como intermediario entre la GUI y la lógica de dominio (CryptoBro).
    Maneja la lógica de negocio adicional como la generación de passphrases mnemotécnicas.
    """
    def __init__(self):
        self.crypto_bro = CryptoBro()
    
    def generate_mnemonic_passphrase(self, num_words: int = 3) -> str:
        """
        Genera una passphrase aleatoria utilizando una lista de palabras.
        
        Args:
            num_words: Número de palabras en la frase.
            
        Returns:
            Una cadena de palabras unidas por guiones (e.g. 'casa-perro-lago').
        """
        json_path = os.path.join('data', 'words.json')
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                words = json.load(f)
            return "-".join(random.sample(words, num_words))
        except Exception as e:
            # Fallback if file not found
            print(f"Error loading words: {e}")
            return f"word{random.randint(100,999)}-secure-{random.randint(100,999)}"

    def generate_hash(self, message: str) -> str:
        """Genera el hash SHA-256 de un mensaje."""
        return self.crypto_bro.generateHash(message)
    
    def verify_hash(self, message: str, hash: str) -> bool:
        """Verifica si un mensaje corresponde a un hash dado."""
        return self.crypto_bro.verifyHash(message, hash)
    
    def generate_key(self) -> str:
        """Genera una clave de encriptación segura."""
        return self.crypto_bro.generateKey()
    
    def encrypt_message(self, message: str, key: str,generated:bool=False) -> str:
        """Encripta un mensaje de texto."""
        return self.crypto_bro.encryptMessage(message, key, generated=generated)
    
    def decrypt_message(self, encrypted_message: str, key: str) -> str:
        """Desencripta un mensaje de texto."""
        return self.crypto_bro.decryptMessage(encrypted_message, key)   
    
    def encryptFile(self, file_path: str, key: str,generated:bool=False) -> tuple[str, str]:
        """Encripta un archivo físico."""
        return self.crypto_bro.encryptFile(file_path, key, generated=generated)
    
    def decryptFile(self, file_path: str, key: str,extension:str,generated:bool=False) -> None:
        """Desencripta un archivo físico."""
        self.crypto_bro.decryptFile(file_path, key,extension=extension, generated=generated)
    
    def generate_and_store_key(self, hash: str,key:str, extension: str, generated:bool = False) -> str:
        """Genera y almacena una clave en la base de datos segura."""
        return self.crypto_bro.generate_and_store_key(hash,key, extension, generated=generated)
    
    def getItemByHash(self, hash: str) -> SecureData:
        """Obtiene un registro por su hash."""
        return self.crypto_bro.getItemByHash(hash)         
    
    def delete_key_by_id(self, item_id: int) -> None: 
        """Elimina una clave por su ID."""
        self.crypto_bro.delete_key_by_id(item_id)     
    
    def getAllItems(self) -> list:
        """Obtiene todas las claves almacenadas."""
        return self.crypto_bro.getAllItems()
