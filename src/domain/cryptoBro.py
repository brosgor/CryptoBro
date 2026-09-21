
import base64
import hashlib
import os
import secrets
import struct
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from repository.database import Database
from models.secure_data import SecureData
from domain.vault import Vault

# .bros v1: MAGIC + VER=1 + salt + ext_len + ext + fernet_token
# .bros v2: MAGIC + VER=2 + salt + name_len + original_basename + fernet_token
# .bros v3: MAGIC + VER=3 + salt + name_len + name + chunk_size + chunks
#   chunk = ct_len(4) + nonce(12) + ciphertext+tag  (AES-256-GCM, streamed)
_BROS_MAGIC = b"BROS"
_BROS_VER = 3
_CHUNK_SIZE = 1024 * 1024  # 1 MiB — RAM acotada aunque el archivo sea de cientos de GB


class CryptoBro:
    """Lógica criptográfica AES/Fernet + PBKDF2. La BD vive detrás de Vault."""

    def __init__(self, vault: Vault):
        self.vault = vault
        self.db = Database(
            vault.db_path,
            on_write=vault.flush,
            conn=vault.db_conn,
            lock=vault._db_lock,
        )
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

    @staticmethod
    def _raw_key(fernet_key: str) -> bytes:
        return base64.urlsafe_b64decode(fernet_key.encode("ascii"))

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
                raise ValueError("Formato de mensaje cifrado inválido (falta el salt)") from e
            encrypted_message = encrypted_message[32:]
            key, _ = self._deriveKey(key, salt)

        fernet = Fernet(key.encode())
        decrypted_message = fernet.decrypt(encrypted_message.encode())
        return decrypted_message.decode()

    def encryptFile(self, file_path: str, key: str, generated: bool = False) -> tuple[str, str, str]:
        """Cifra a <hex opaco>.bros en chunks (v3); el nombre original va dentro.
        Returns: (extension_encrypted, key_used, bros_path)
        """
        salt = b""
        if not generated:
            key, salt = self._deriveKey(key)
        else:
            salt = b"\0" * 16

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

        aesgcm = AESGCM(self._raw_key(key))
        with open(file_path, "rb") as fin, open(encrypted_path, "wb") as fout:
            fout.write(_BROS_MAGIC)
            fout.write(bytes([_BROS_VER]))
            fout.write(salt)
            fout.write(struct.pack(">H", len(name_bytes)))
            fout.write(name_bytes)
            fout.write(struct.pack(">I", _CHUNK_SIZE))

            idx = 0
            while True:
                plain = fin.read(_CHUNK_SIZE)
                # un chunk vacío solo si el archivo es 0 bytes
                if not plain and idx > 0:
                    break
                nonce = os.urandom(12)
                aad = struct.pack(">Q", idx)
                ct = aesgcm.encrypt(nonce, plain, aad)
                fout.write(struct.pack(">I", len(ct)))
                fout.write(nonce)
                fout.write(ct)
                idx += 1
                if len(plain) < _CHUNK_SIZE:
                    break

        _, ext = os.path.splitext(original_name)
        extension_encrypted = self.encryptMessage(message=ext, key=key, generated=True)
        return extension_encrypted, key, encrypted_path

    def decryptFile(
        self, file_path: str, key: str, extension: str = None, generated: bool = False
    ) -> str:
        """Descifra .bros (v1/v2 Fernet o v3 AES-GCM streaming). Devuelve la ruta."""
        from domain.paths import plain_dir

        directory = str(plain_dir())

        with open(file_path, "rb") as encrypted_file:
            header = encrypted_file.read(5)
            if header[:4] != _BROS_MAGIC:
                return self._decrypt_legacy_blob(
                    header + encrypted_file.read(),
                    key,
                    extension,
                    generated,
                    directory,
                    file_path,
                )

            ver = header[4]
            file_salt = encrypted_file.read(16)

            if ver >= 3:
                name_len = struct.unpack(">H", encrypted_file.read(2))[0]
                original_name = encrypted_file.read(name_len).decode("utf-8")
                chunk_size = struct.unpack(">I", encrypted_file.read(4))[0]
                if chunk_size == 0 or chunk_size > 64 * 1024 * 1024:
                    raise ValueError("chunk_size inválido en .bros v3")

                if not generated:
                    key, _ = self._deriveKey(key, salt=file_salt)

                decrypted_path = self._unique_out_path(
                    os.path.join(directory, os.path.basename(original_name))
                )
                aesgcm = AESGCM(self._raw_key(key))
                with open(decrypted_path, "wb") as fout:
                    idx = 0
                    while True:
                        len_b = encrypted_file.read(4)
                        if not len_b:
                            break
                        if len(len_b) < 4:
                            raise ValueError(".bros v3 truncado")
                        ct_len = struct.unpack(">I", len_b)[0]
                        nonce = encrypted_file.read(12)
                        ct = encrypted_file.read(ct_len)
                        if len(nonce) < 12 or len(ct) < ct_len:
                            raise ValueError(".bros v3 truncado")
                        plain = aesgcm.decrypt(nonce, ct, struct.pack(">Q", idx))
                        fout.write(plain)
                        idx += 1
                return decrypted_path

            # v1 / v2: Fernet (archivo completo en RAM; solo legado)
            if ver >= 2:
                name_len = struct.unpack(">H", encrypted_file.read(2))[0]
                original_name = encrypted_file.read(name_len).decode("utf-8")
                encrypted = encrypted_file.read()
                ext_from_file = None
            else:
                original_name = None
                ext_len = struct.unpack(">H", encrypted_file.read(2))[0]
                ext_from_file = encrypted_file.read(ext_len).decode("utf-8")
                encrypted = encrypted_file.read()

        if not generated:
            key, _ = self._deriveKey(key, salt=file_salt)

        fernet = Fernet(key.encode())
        decrypted = fernet.decrypt(encrypted)

        if original_name:
            decrypted_path = self._unique_out_path(
                os.path.join(directory, os.path.basename(original_name))
            )
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
            decrypted_path = self._unique_out_path(base + extension_decrypted)

        with open(decrypted_path, "wb") as decrypted_file:
            decrypted_file.write(decrypted)
        return decrypted_path

    def _decrypt_legacy_blob(
        self, blob: bytes, key: str, extension, generated: bool, directory: str, file_path: str
    ) -> str:
        file_salt = blob[:16]
        encrypted = blob[16:]
        if not generated:
            key, _ = self._deriveKey(key, salt=file_salt)
        fernet = Fernet(key.encode())
        decrypted = fernet.decrypt(encrypted)
        base, _ = os.path.splitext(file_path)
        if extension is not None:
            extension_decrypted = self.decryptMessage(
                encrypted_message=extension, key=key, generated=True
            )
        else:
            extension_decrypted = ".gor"
        decrypted_path = self._unique_out_path(base + extension_decrypted)
        with open(decrypted_path, "wb") as f:
            f.write(decrypted)
        return decrypted_path

    @staticmethod
    def _unique_out_path(decrypted_path: str) -> str:
        if not os.path.exists(decrypted_path):
            return decrypted_path
        stem, ext = os.path.splitext(decrypted_path)
        n = 1
        while os.path.exists(f"{stem}_restored{n}{ext}"):
            n += 1
        return f"{stem}_restored{n}{ext}"

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


def _shred_file(path: str, chunk: int = _CHUNK_SIZE) -> None:
    """Sobrescribe con aleatorio por chunks y borra (sin cargar el archivo entero)."""
    if not os.path.exists(path):
        return
    size = os.path.getsize(path)
    with open(path, "r+b") as f:
        left = size
        while left > 0:
            n = min(chunk, left)
            f.write(os.urandom(n))
            left -= n
        f.flush()
        os.fsync(f.fileno())
    os.remove(path)


if __name__ == "__main__":
    # ponytail: self-check streaming roundtrip
    import sys
    import tempfile
    from pathlib import Path

    _root = Path(__file__).resolve().parents[1]
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

    import domain.paths as paths

    tmp = Path(tempfile.mkdtemp())
    cipher, plain = tmp / "c", tmp / "p"
    cipher.mkdir()
    plain.mkdir()
    paths.cipher_dir = lambda: cipher
    paths.plain_dir = lambda: plain
    cb = CryptoBro.__new__(CryptoBro)
    key = Fernet.generate_key().decode()
    src = tmp / "x.bin"
    payload = os.urandom(_CHUNK_SIZE + 99)
    src.write_bytes(payload)
    _, k, bros = cb.encryptFile(str(src), key, generated=True)
    out = Path(cb.decryptFile(bros, k, generated=True))
    assert out.read_bytes() == payload
    print("cryptoBro streaming ok")
