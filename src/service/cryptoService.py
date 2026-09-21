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
        self, file_path: str, key: str, extension: str | None = None, generated: bool = False,
        wipe_cipher: bool = True,
    ) -> str:
        out = self.crypto_bro.decryptFile(
            file_path, key, extension=extension, generated=generated
        )
        # wipe_cipher=False en cápsulas: el .bros es bodega persistente
        if (
            wipe_cipher
            and os.path.abspath(file_path) != os.path.abspath(out)
            and os.path.exists(file_path)
        ):
            from domain.cryptoBro import _shred_file

            try:
                _shred_file(file_path)
            except OSError:
                pass
        return out

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
        password: str | None = None,
    ) -> tuple:
        """
        Complementarios (offline):
        - bloqueo = calendario hasta unlock_at (años/días/horas/min).
        - descifrado = puzzle CPU (min/seg) al Resolver, tras vencer el bloqueo.
        - password opcional: tras calendario/puzzle pide contraseña para abrir el .bros.
        Al menos uno de bloqueo/descifrado debe ser > 0.
        """
        from domain.timelock import seal_to_str, wrap_key_with_password

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

        pw = (password or "").strip()
        use_pw = bool(pw)

        key = self.generate_key()
        extension, used_key, bros_path = self.encryptFile(file_path, key, generated=True)
        unlock_at = (datetime.now() + lock).isoformat(timespec="seconds")
        name = label.strip() or os.path.basename(file_path)

        inner = used_key
        if use_pw:
            inner = wrap_key_with_password(used_key, pw)

        if decrypt_secs > 0:
            stored = seal_to_str(inner, decrypt_secs, password_protected=use_pw)
        else:
            stored = inner

        cid = self.crypto_bro.addCapsule(name, bros_path, stored, unlock_at, extension)

        if delete_original and os.path.exists(file_path):
            from domain.cryptoBro import _shred_file

            _shred_file(file_path)

        return cid, unlock_at, bros_path, int(lock_secs), int(decrypt_secs), use_pw

    def get_all_capsules(self) -> list:
        return self.crypto_bro.getAllCapsules()

    def capsule_needs_password(self, capsule_id: int) -> bool:
        from domain.timelock import needs_password

        cap = self.crypto_bro.getCapsuleById(capsule_id)
        if not cap:
            return False
        return needs_password(cap.key)

    def release_capsule_secret(self, capsule_id: int, progress=None) -> str:
        """Calendario + puzzle → secreto interno (clave o envoltorio con contraseña)."""
        from domain.timelock import is_puzzle, open_puzzle

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

        if is_puzzle(cap.key):
            return open_puzzle(cap.key, progress=progress)
        return cap.key

    def open_capsule_with_secret(
        self, capsule_id: int, secret: str, password: str | None = None
    ) -> str:
        """Descifra el .bros con el secreto liberado (+ contraseña si aplica)."""
        from domain.timelock import is_password_wrap, unwrap_key_with_password
        from cryptography.fernet import InvalidToken

        cap = self.crypto_bro.getCapsuleById(capsule_id)
        if not cap:
            raise ValueError("Cápsula no encontrada")

        try:
            if is_password_wrap(secret):
                if not password:
                    raise ValueError("Esta cápsula requiere contraseña")
                real_key = unwrap_key_with_password(secret, password)
            else:
                real_key = secret

            return self.decryptFile(
                cap.bros_path,
                real_key,
                extension=cap.extension,
                generated=True,
                wipe_cipher=False,  # bodega: el .bros permanece
            )
        except InvalidToken as e:
            raise ValueError(
                "No se pudo descifrar el archivo (clave, puzzle o contraseña incorrectos)."
            ) from e

    def unlock_capsule(
        self, capsule_id: int, progress=None, password: str | None = None
    ) -> str:
        secret = self.release_capsule_secret(capsule_id, progress=progress)
        return self.open_capsule_with_secret(capsule_id, secret, password=password)

    def delete_capsule(self, capsule_id: int, wipe_bros: bool = False) -> None:
        cap = self.crypto_bro.getCapsuleById(capsule_id)
        self.crypto_bro.deleteCapsule(capsule_id)
        if wipe_bros and cap and cap.bros_path and os.path.exists(cap.bros_path):
            from domain.cryptoBro import _shred_file

            try:
                _shred_file(cap.bros_path)
            except OSError:
                pass

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

    def hash_file(self, path: str, chunk: int = 1024 * 1024, progress=None) -> dict:
        md5 = hashlib.md5()
        sha1 = hashlib.sha1()
        sha256 = hashlib.sha256()
        total = max(os.path.getsize(path), 1)
        done = 0
        with open(path, "rb") as f:
            while True:
                block = f.read(chunk)
                if not block:
                    break
                md5.update(block)
                sha1.update(block)
                sha256.update(block)
                done += len(block)
                if progress:
                    progress(done, total)
        if progress:
            progress(total, total)
        return {
            "md5": md5.hexdigest(),
            "sha1": sha1.hexdigest(),
            "sha256": sha256.hexdigest(),
        }

    def hash_directory(self, dir_path: str, progress=None) -> dict:
        """
        Hash de carpeta: concatena 'relpath\\0sha256\\n' ordenado y hashea ese manifiesto.
        Así el digest refleja contenido + estructura (no solo un archivo suelto).
        """
        root = os.path.abspath(dir_path)
        if not os.path.isdir(root):
            raise ValueError("No es una carpeta")

        files = []
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in sorted(filenames):
                full = os.path.join(dirpath, name)
                if os.path.isfile(full):
                    files.append(full)

        if not files:
            raise ValueError("La carpeta no tiene archivos")

        total = len(files)
        lines = []
        for i, full in enumerate(files, start=1):
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            digest = self.hash_file(full)["sha256"]
            lines.append(f"{rel}\0{digest}\n")
            if progress:
                progress(i, total)

        manifest = "".join(sorted(lines)).encode("utf-8")
        result = self.hash_bytes(manifest)
        result["files"] = total
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

    def save_vault_now(self) -> None:
        """Persiste la BD en memoria al .gor de inmediato."""
        self.vault.flush()

    def vault_info(self) -> dict:
        return self.vault.vault_info()

    def set_vault_description(self, description: str) -> None:
        self.vault.set_description(description)

    def hash_vault_file(self, progress=None) -> dict:
        return self.hash_file(str(self.vault.gor_path), progress=progress)

    def list_bodega(self) -> list:
        from pathlib import Path

        from domain.cryptoBro import read_bros_name
        from domain.paths import cipher_dir

        items = []
        for p in sorted(Path(cipher_dir()).glob("*.bros")):
            if not p.is_file():
                continue
            try:
                st = p.stat()
                items.append(
                    {
                        "path": str(p),
                        "opaque": p.name,
                        "original": read_bros_name(str(p)),
                        "size": st.st_size,
                        "mtime": datetime.fromtimestamp(st.st_mtime).isoformat(
                            timespec="seconds"
                        ),
                    }
                )
            except OSError:
                continue
        return items

    def import_bros_file(self, src: str) -> str:
        import shutil
        from pathlib import Path

        from domain.paths import cipher_dir

        src_p = Path(src)
        if not src_p.is_file():
            raise FileNotFoundError("Archivo no encontrado")
        d = cipher_dir()
        d.mkdir(parents=True, exist_ok=True)
        dest = d / src_p.name
        if dest.resolve() == src_p.resolve():
            return str(dest)
        if dest.exists():
            stem = src_p.stem
            n = 1
            while (d / f"{stem}_{n}.bros").exists():
                n += 1
            dest = d / f"{stem}_{n}.bros"
        shutil.copy2(src_p, dest)
        return str(dest)

    def export_capsule(self, capsule_id: int, dest: str) -> str:
        import zipfile
        from pathlib import Path

        cap = self.crypto_bro.getCapsuleById(capsule_id)
        if not cap:
            raise ValueError("Cápsula no encontrada")
        src = Path(cap.bros_path)
        if not src.is_file():
            raise FileNotFoundError(f"No está el .bros: {cap.bros_path}")
        dest = Path(dest)
        if dest.suffix.lower() != ".cap":
            dest = dest.with_suffix(".cap")
        payload = src.read_bytes()
        meta = {
            "v": 1,
            "app": "CryptoBro",
            "format": "cap",
            "label": cap.label,
            "unlock_at": cap.unlock_at,
            "extension": cap.extension,
            "key": cap.key,
            "created": datetime.now().isoformat(timespec="seconds"),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
        with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("capsule.json", json.dumps(meta, indent=2))
            zf.writestr("payload.bros", payload)
        return str(dest)

    def import_capsule(self, src: str) -> int:
        import zipfile
        from pathlib import Path

        from domain.paths import cipher_dir

        src = Path(src)
        if not src.is_file():
            raise FileNotFoundError("Archivo no encontrado")
        try:
            with zipfile.ZipFile(src, "r") as zf:
                meta = json.loads(zf.read("capsule.json"))
                payload = zf.read("payload.bros")
        except Exception as e:
            raise ValueError("Copia de cápsula inválida (.cap)") from e
        if meta.get("sha256") and hashlib.sha256(payload).hexdigest() != meta["sha256"]:
            raise ValueError("Integridad fallida: el .cap está corrupto o alterado")
        if not meta.get("key"):
            raise ValueError("La cápsula no trae clave")
        d = cipher_dir()
        d.mkdir(parents=True, exist_ok=True)
        bros_path = str(d / (secrets.token_hex(16) + ".bros"))
        Path(bros_path).write_bytes(payload)
        cid = self.crypto_bro.addCapsule(
            meta.get("label", "importada"),
            bros_path,
            meta["key"],
            meta.get("unlock_at") or datetime.now().isoformat(timespec="seconds"),
            meta.get("extension", ""),
        )
        return cid

    def write_recovery_par(self, phrase: str, bros_path: str) -> str:
        token = self.vault.encrypt_recovery(phrase)
        par_path = os.path.splitext(bros_path)[0] + ".par"
        with open(par_path, "w", encoding="utf-8") as f:
            json.dump({"v": 2, "kind": "recovery", "data": token}, f)
        return par_path

    def read_recovery_par(self, par_path: str) -> str:
        with open(par_path, "r", encoding="utf-8") as f:
            raw = f.read().strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return raw  # legado: texto plano
        if isinstance(data, dict) and data.get("v") == 2 and data.get("kind") == "recovery":
            from cryptography.fernet import InvalidToken

            try:
                return self.vault.decrypt_recovery(data["data"])
            except InvalidToken:
                raise ValueError("El .par está cifrado con otra bóveda (clave distinta)")
        return raw

    def lock(self) -> None:
        self.vault.lock()
