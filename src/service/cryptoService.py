from domain.cryptoBro import CryptoBro
from domain.vault import Vault
from models.secure_data import SecureData
from domain.paths import WORDS_JSON
import json
import secrets
import os
import hashlib
from datetime import datetime, timedelta


class CryptoService:
    """Intermediario GUI ↔ dominio. Requiere Vault ya desbloqueado."""

    def __init__(self, vault: Vault):
        self.vault = vault
        self.crypto_bro = CryptoBro(vault)

    def generate_mnemonic_passphrase(self, num_words: int = 6) -> str:
        try:
            with open(WORDS_JSON, "r", encoding="utf-8") as f:
                words = json.load(f)
            return "-".join(secrets.choice(words) for _ in range(num_words))
        except Exception:
            return "-".join(secrets.token_hex(3) for _ in range(num_words))

    def generate_hash(self, message: str) -> str:
        return self.crypto_bro.generateHash(message)

    def verify_hash(self, message: str, hash: str) -> bool:
        return self.crypto_bro.verifyHash(message, hash)

    def generate_key(self) -> str:
        return self.crypto_bro.generateKey()

    def encrypt_message(self, message: str, key: str, generated: bool = False) -> str:
        return self.crypto_bro.encryptMessage(message, key, generated=generated)

    def decrypt_message(self, encrypted_message: str, key: str) -> str:
        return self.crypto_bro.decryptMessage(encrypted_message, key)

    def encryptFile(self, file_path: str, key: str, generated: bool = False) -> tuple[str, str, str]:
        return self.crypto_bro.encryptFile(file_path, key, generated=generated)

    def decryptFile(
        self, file_path: str, key: str, extension: str, generated: bool = False
    ) -> str:
        return self.crypto_bro.decryptFile(
            file_path, key, extension=extension, generated=generated
        )

    def generate_and_store_key(
        self, hash: str, key: str, extension: str, generated: bool = False
    ) -> str:
        return self.crypto_bro.generate_and_store_key(hash, key, extension, generated=generated)

    def getItemByHash(self, hash: str) -> SecureData:
        return self.crypto_bro.getItemByHash(hash)

    def delete_key_by_id(self, item_id: int) -> None:
        self.crypto_bro.delete_key_by_id(item_id)

    def getAllItems(self) -> list:
        return self.crypto_bro.getAllItems()

    def save_message(self, title: str, message: str, key: str) -> None:
        encrypted = self.encrypt_message(message, key)
        self.crypto_bro.saveMessage(title, encrypted)

    def update_message(self, msg_id: int, title: str, message: str, key: str) -> None:
        encrypted = self.encrypt_message(message, key)
        self.crypto_bro.updateMessage(msg_id, title, encrypted)

    def get_all_messages(self) -> list:
        return self.crypto_bro.getAllMessages()

    def delete_message(self, msg_id: int) -> None:
        self.crypto_bro.deleteMessage(msg_id)

    def create_time_capsule(
        self,
        file_path: str,
        label: str,
        years=0,
        days=0,
        hours=0,
        lock_minutes=0,
        decrypt_minutes=0,
        decrypt_seconds=0,
        delete_original=False,
    ) -> tuple:
        """
        Complementarios (offline):
        - bloqueo = calendario hasta unlock_at (años/días/horas/min).
        - descifrado = puzzle CPU (min/seg) al Resolver, tras vencer el bloqueo.
        Al menos uno debe ser > 0.
        """
        from domain.timelock import seal_to_str

        lock = timedelta(
            days=years * 365 + days, hours=hours, minutes=lock_minutes
        )
        decrypt = timedelta(minutes=decrypt_minutes, seconds=decrypt_seconds)
        lock_secs = lock.total_seconds()
        decrypt_secs = decrypt.total_seconds()

        if lock_secs <= 0 and decrypt_secs <= 0:
            raise ValueError(
                "Indica tiempo a bloquear y/o tiempo de descifrado (al menos uno)."
            )
        if decrypt_secs > 3600:
            raise ValueError("Tiempo de descifrado: máximo 60 minutos de CPU")

        key = self.generate_key()
        extension, used_key, bros_path = self.encryptFile(file_path, key, generated=True)
        unlock_at = (datetime.now() + lock).isoformat(timespec="seconds")
        name = label.strip() or os.path.basename(file_path)

        if decrypt_secs > 0:
            stored = seal_to_str(used_key, decrypt_secs)
        else:
            # solo calendario: clave en bóveda
            stored = used_key

        cid = self.crypto_bro.addCapsule(name, bros_path, stored, unlock_at, extension)

        if delete_original and os.path.exists(file_path):
            size = os.path.getsize(file_path)
            with open(file_path, "wb") as f:
                f.write(os.urandom(size))
            os.remove(file_path)

        return cid, unlock_at, bros_path, int(lock_secs), int(decrypt_secs)

    def get_all_capsules(self) -> list:
        return self.crypto_bro.getAllCapsules()

    def unlock_capsule(self, capsule_id: int, progress=None) -> str:
        from domain.timelock import is_puzzle, open_puzzle
        from cryptography.fernet import InvalidToken

        cap = self.crypto_bro.getCapsuleById(capsule_id)
        if not cap:
            raise ValueError("Cápsula no encontrada")
        if not os.path.exists(cap.bros_path):
            raise FileNotFoundError(f"No está el .bros: {cap.bros_path}")

        unlock_at = datetime.fromisoformat(cap.unlock_at)
        if datetime.now() < unlock_at:
            raise ValueError(
                "Aún está bloqueada por calendario.\n"
                f"Se podrá resolver/abrir desde: {cap.unlock_at}\n"
                "(Depende del reloj del PC.)"
            )

        try:
            if is_puzzle(cap.key):
                real_key = open_puzzle(cap.key, progress=progress)
            else:
                real_key = cap.key

            return self.decryptFile(
                cap.bros_path, real_key, extension=cap.extension, generated=True
            )
        except InvalidToken as e:
            raise ValueError(
                "No se pudo descifrar el archivo (clave o puzzle incorrectos)."
            ) from e

    def delete_capsule(self, capsule_id: int) -> None:
        self.crypto_bro.deleteCapsule(capsule_id)

    def export_vault_backup(self, dest: str):
        return self.vault.export_backup(dest)

    def change_vault_password(self, old: str, new: str) -> None:
        self.vault.change_password(old, new)

    def reset_vault_contents(self, password: str) -> None:
        self.vault.reset_contents(password)
        self.crypto_bro = CryptoBro(self.vault)

    def delete_current_vault(self, wipe_file: bool = True) -> None:
        name = self.vault.name
        self.vault.lock()
        self.vault.delete_vault(name, wipe_file=wipe_file)

    def forget_current_vault(self) -> None:
        """Quita de la lista; conserva el .gor en disco."""
        self.delete_current_vault(wipe_file=False)

    def hash_bytes(self, data: bytes) -> dict:
        return {
            "md5": hashlib.md5(data).hexdigest(),
            "sha1": hashlib.sha1(data).hexdigest(),
            "sha256": hashlib.sha256(data).hexdigest(),
        }

    def hash_file(self, path: str, chunk: int = 1024 * 1024) -> dict:
        md5 = hashlib.md5()
        sha1 = hashlib.sha1()
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                block = f.read(chunk)
                if not block:
                    break
                md5.update(block)
                sha1.update(block)
                sha256.update(block)
        return {
            "md5": md5.hexdigest(),
            "sha1": sha1.hexdigest(),
            "sha256": sha256.hexdigest(),
        }

    def hash_directory(self, dir_path: str) -> dict:
        """
        Hash de carpeta: concatena 'relpath\\0sha256\\n' ordenado y hashea ese manifiesto.
        Así el digest refleja contenido + estructura (no solo un archivo suelto).
        """
        root = os.path.abspath(dir_path)
        if not os.path.isdir(root):
            raise ValueError("No es una carpeta")

        lines = []
        file_count = 0
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in sorted(filenames):
                full = os.path.join(dirpath, name)
                if not os.path.isfile(full):
                    continue
                rel = os.path.relpath(full, root).replace(os.sep, "/")
                digest = self.hash_file(full)["sha256"]
                lines.append(f"{rel}\0{digest}\n")
                file_count += 1

        if file_count == 0:
            raise ValueError("La carpeta no tiene archivos")

        manifest = "".join(sorted(lines)).encode("utf-8")
        result = self.hash_bytes(manifest)
        result["files"] = file_count
        return result

    def generate_password(
        self,
        length: int = 20,
        lower: bool = True,
        upper: bool = True,
        digits: bool = True,
        symbols: bool = True,
    ) -> dict:
        """
        Contraseña CSPRNG (secrets). Devuelve texto + bits de entropía aprox.
        """
        import math
        import string

        if length < 8:
            raise ValueError("Longitud mínima: 8")
        alphabet = ""
        if lower:
            alphabet += string.ascii_lowercase
        if upper:
            alphabet += string.ascii_uppercase
        if digits:
            alphabet += string.digits
        if symbols:
            alphabet += "!@#$%^&*()-_=+[]{}:,.?/"
        if not alphabet:
            raise ValueError("Elige al menos un tipo de carácter")

        # garantiza al menos un char de cada clase elegida
        required = []
        if lower:
            required.append(secrets.choice(string.ascii_lowercase))
        if upper:
            required.append(secrets.choice(string.ascii_uppercase))
        if digits:
            required.append(secrets.choice(string.digits))
        if symbols:
            required.append(secrets.choice("!@#$%^&*()-_=+[]{}:,.?/"))
        if length < len(required):
            length = len(required)

        rest = [secrets.choice(alphabet) for _ in range(length - len(required))]
        chars = required + rest
        # shuffle seguro
        for i in range(len(chars) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            chars[i], chars[j] = chars[j], chars[i]
        password = "".join(chars)
        entropy = length * math.log2(len(alphabet))
        return {
            "password": password,
            "entropy_bits": round(entropy, 1),
            "alphabet_size": len(alphabet),
            "length": length,
        }

    def generate_passphrase_info(self, num_words: int = 8) -> dict:
        import math

        phrase = self.generate_mnemonic_passphrase(num_words)
        try:
            with open(WORDS_JSON, "r", encoding="utf-8") as f:
                n = len(json.load(f))
        except Exception:
            n = 1000
        entropy = num_words * math.log2(max(n, 2))
        return {
            "password": phrase,
            "entropy_bits": round(entropy, 1),
            "alphabet_size": n,
            "length": num_words,
            "kind": "passphrase",
        }

    def lock(self) -> None:
        self.vault.lock()
