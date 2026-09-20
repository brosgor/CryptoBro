
import base64
import hashlib
import os
import secrets
import struct
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from repository.database import Database
from models.secure_data import SecureData
from domain.vault import Vault

# .bros v1: MAGIC + VER=1 + salt + ext_len + ext + token
# .bros v2: MAGIC + VER=2 + salt + name_len + original_basename + token
_BROS_MAGIC = b"BROS"
_BROS_VER = 2


class CryptoBro:
    """Lógica criptográfica AES/Fernet + PBKDF2. La BD vive detrás de Vault."""

    def __init__(self, vault: Vault):
        self.vault = vault
        self.db = Database(vault.db_path)
        self._import_legacy_if_any()

    def _import_legacy_if_any(self) -> None:
        from domain.paths import DATA

        legacy = DATA / "secure.db"
        if legacy.exists() and legacy.stat().st_size > 0:
            try:
                self.vault._merge_legacy(legacy)
            except Exception:
                pass

    def _deriveKey(self, key: str, salt: bytes = None):
        if salt is None:
            salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key_derived = base64.urlsafe_b64encode(kdf.derive(key.encode()))
        return key_derived.decode(), salt

    def generateHash(self, message: str) -> str:
        return hashlib.sha256(message.encode()).hexdigest()

    def verifyHash(self, message: str, hash: str) -> bool:
        return self.generateHash(message) == hash

    def generateKey(self) -> str:
        return Fernet.generate_key().decode()

    def encryptMessage(self, message: str, key: str, generated: bool = False) -> str:
        salt_hex = ""
        if not generated:
            key, salt = self._deriveKey(key)
            salt_hex = salt.hex()
        fernet = Fernet(key.encode())
        encrypted_message = fernet.encrypt(message.encode())
        return salt_hex + encrypted_message.decode()

    def decryptMessage(self, encrypted_message: str, key: str, generated: bool = False) -> str:
        if not generated:
            salt_hex = encrypted_message[:32]
            try:
                salt = bytes.fromhex(salt_hex)
            except ValueError as e:
                raise ValueError("Invalid encrypted message format (missing salt)") from e
            encrypted_message = encrypted_message[32:]
            key, _ = self._deriveKey(key, salt)

        fernet = Fernet(key.encode())
        decrypted_message = fernet.decrypt(encrypted_message.encode())
        return decrypted_message.decode()

    def encryptFile(self, file_path: str, key: str, generated: bool = False) -> tuple[str, str, str]:
        """Cifra a <hex opaco>.bros; el nombre original va dentro (v2).
        Returns: (extension_encrypted, key_used, bros_path)
        """
        salt = b""
        if not generated:
            key, salt = self._deriveKey(key)
        else:
            salt = b"\0" * 16

        fernet = Fernet(key.encode())
        with open(file_path, "rb") as file:
            original = file.read()
        encrypted = fernet.encrypt(original)

        original_name = os.path.basename(file_path)
        name_bytes = original_name.encode("utf-8")
        if len(name_bytes) > 65535:
            raise ValueError("Nombre de archivo demasiado largo")

        directory = str(__import__("domain.paths", fromlist=["cipher_dir"]).cipher_dir())
        while True:
            opaque = secrets.token_hex(16) + ".bros"
            encrypted_path = os.path.join(directory, opaque)
            if not os.path.exists(encrypted_path):
                break

        with open(encrypted_path, "wb") as encrypted_file:
            encrypted_file.write(_BROS_MAGIC)
            encrypted_file.write(bytes([_BROS_VER]))
            encrypted_file.write(salt)
            encrypted_file.write(struct.pack(">H", len(name_bytes)))
            encrypted_file.write(name_bytes)
            encrypted_file.write(encrypted)

        _, ext = os.path.splitext(original_name)
        extension_encrypted = self.encryptMessage(message=ext, key=key, generated=True)
        return extension_encrypted, key, encrypted_path

    def decryptFile(
        self, file_path: str, key: str, extension: str = None, generated: bool = False
    ) -> str:
        """Descifra .bros y restaura el nombre original si es v2. Devuelve la ruta."""
        original_name = None
        ext_from_file = None

        with open(file_path, "rb") as encrypted_file:
            header = encrypted_file.read(5)
            if header[:4] == _BROS_MAGIC:
                ver = header[4]
                file_salt = encrypted_file.read(16)
                if ver >= 2:
                    name_len = struct.unpack(">H", encrypted_file.read(2))[0]
                    original_name = encrypted_file.read(name_len).decode("utf-8")
                    encrypted = encrypted_file.read()
                else:
                    ext_len = struct.unpack(">H", encrypted_file.read(2))[0]
                    ext_from_file = encrypted_file.read(ext_len).decode("utf-8")
                    encrypted = encrypted_file.read()
            else:
                rest = header + encrypted_file.read()
                file_salt = rest[:16]
                encrypted = rest[16:]

        if not generated:
            key, _ = self._deriveKey(key, salt=file_salt)

        fernet = Fernet(key.encode())
        decrypted = fernet.decrypt(encrypted)
        from domain.paths import plain_dir

        directory = str(plain_dir())

        if original_name:
            # evita path traversal
            original_name = os.path.basename(original_name)
            decrypted_path = os.path.join(directory, original_name)
        else:
            base, _ = os.path.splitext(file_path)
            if extension is not None:
                extension_decrypted = self.decryptMessage(
                    encrypted_message=extension, key=key, generated=True
                )
            elif ext_from_file is not None:
                extension_decrypted = ext_from_file
            else:
                extension_decrypted = ".gor"
            decrypted_path = base + extension_decrypted

        if os.path.exists(decrypted_path):
            stem, ext = os.path.splitext(decrypted_path)
            n = 1
            while os.path.exists(f"{stem}_restored{n}{ext}"):
                n += 1
            decrypted_path = f"{stem}_restored{n}{ext}"

        with open(decrypted_path, "wb") as decrypted_file:
            decrypted_file.write(decrypted)
        return decrypted_path

    def generate_and_store_key(
        self, hash: str, key: str, extension: str, generated: bool = False
    ) -> str:
        if not generated:
            key, _ = self._deriveKey(key)
        self.db.addItem(hash=hash, key=key, extension=extension)
        return key

    def getItemByHash(self, hash: str) -> SecureData:
        return self.db.getItemByHash(hash)

    def delete_key_by_id(self, item_id: int) -> None:
        self.db.deleteItemById(item_id)

    def getAllItems(self) -> list:
        return self.db.getAllItems()

    def saveMessage(self, title: str, encrypted_message: str) -> int:
        return self.db.addMessage(title, encrypted_message)

    def updateMessage(self, msg_id: int, title: str, encrypted_message: str) -> int:
        return self.db.updateMessage(msg_id, title, encrypted_message)

    def getAllMessages(self) -> list:
        return self.db.getAllMessages()

    def getMessageById(self, msg_id: int):
        return self.db.getMessageById(msg_id)

    def deleteMessage(self, msg_id: int):
        return self.db.deleteMessage(msg_id)

    def addCapsule(self, label, bros_path, key, unlock_at, extension) -> int:
        return self.db.addCapsule(label, bros_path, key, unlock_at, extension)

    def getAllCapsules(self) -> list:
        return self.db.getAllCapsules()

    def getCapsuleById(self, capsule_id: int):
        return self.db.getCapsuleById(capsule_id)

    def deleteCapsule(self, capsule_id: int) -> int:
        return self.db.deleteCapsule(capsule_id)
