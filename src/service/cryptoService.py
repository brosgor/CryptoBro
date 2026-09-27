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

    def encryptFile(
        self,
        file_path: str,
        key: str,
        generated: bool = False,
        progress=None,
        out_ext: str = ".bros",
        out_dir: str | None = None,
    ) -> tuple[str, str, str]:
        return self.crypto_bro.encryptFile(
            file_path,
            key,
            generated=generated,
            progress=progress,
            out_ext=out_ext,
            out_dir=out_dir,
        )

    def decryptFile(
        self,
        file_path: str,
        key: str,
        extension: str | None = None,
        generated: bool = False,
        wipe_cipher: bool = True,
        progress=None,
    ) -> str:
        out = self.crypto_bro.decryptFile(
            file_path,
            key,
            extension=extension,
            generated=generated,
            progress=progress,
        )
        # wipe_cipher=False en cápsulas: el .sbro/.bros es bodega persistente
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

    def seal_key_for_vault(
        self, file_key: str, puzzle_seconds: float, password: str
    ) -> str:
        """Puzzle CPU + contraseña: al abrir → resolver puzzle → pedir password."""
        from domain.timelock import seal_to_str, wrap_key_with_password

        if puzzle_seconds <= 0:
            raise ValueError("El tiempo de puzzle debe ser > 0")
        wrapped = wrap_key_with_password(file_key, password)
        return seal_to_str(wrapped, puzzle_seconds, password_protected=True)

    def release_vault_key(
        self, blob: str, password: str | None = None, progress=None
    ) -> str:
        """Libera clave guardada (puzzle y/o envoltorio de contraseña)."""
        from domain.timelock import (
            is_password_wrap,
            is_puzzle,
            needs_password,
            open_puzzle,
            unwrap_key_with_password,
        )

        secret = blob
        if is_puzzle(secret):
            secret = open_puzzle(secret, progress=progress)
        if needs_password(secret) or is_password_wrap(secret):
            if not password:
                raise ValueError("Se requiere la contraseña de cifrado")
            secret = unwrap_key_with_password(secret, password)
        return secret

    def getItemByHash(self, hash: str) -> SecureData:
        return self.crypto_bro.getItemByHash(hash)

    def delete_key_by_id(self, item_id: int) -> None:
        self.crypto_bro.delete_key_by_id(item_id)

    def getAllItems(self) -> list:
        return self.crypto_bro.getAllItems()

    def save_message(self, title: str, message: str, key: str, folder: str = "") -> None:
        encrypted = self.encrypt_message(message, key)
        folder = folder or ""
        if folder:
            self.crypto_bro.upsertNoteGroup(folder)
        self.crypto_bro.saveMessage(title, encrypted, folder=folder)

    def update_message(
        self,
        msg_id: int,
        title: str,
        message: str,
        key: str,
        folder: str | None = None,
    ) -> None:
        encrypted = self.encrypt_message(message, key)
        if folder:
            self.crypto_bro.upsertNoteGroup(folder)
        self.crypto_bro.updateMessage(msg_id, title, encrypted, folder=folder)

    def get_all_messages(self) -> list:
        return self.crypto_bro.getAllMessages()

    def get_message_folders(self) -> list:
        return self.crypto_bro.getMessageFolders()

    def create_note_group(self, title: str, description: str = "") -> int:
        return self.crypto_bro.addNoteGroup(title, description)

    def update_note_group(self, group_id: int, title: str, description: str) -> None:
        self.crypto_bro.updateNoteGroup(group_id, title, description)

    def get_note_group(self, title: str):
        return self.crypto_bro.getNoteGroupByTitle(title)

    def get_all_note_groups(self) -> list:
        return self.crypto_bro.getAllNoteGroups()

    def delete_note_group(self, title: str, *, move_notes_to_root: bool = True) -> None:
        self.crypto_bro.deleteNoteGroup(title, move_notes_to_root=move_notes_to_root)

    def delete_message(self, msg_id: int) -> None:
        self.crypto_bro.deleteMessage(msg_id)

    def export_note(self, msg_id: int, dest: str) -> str:
        """Exporta nota cifrada (.cnote). Sigue haciendo falta la contraseña de la nota."""
        import json
        from pathlib import Path

        msg = self.crypto_bro.getMessageById(msg_id)
        if not msg:
            raise ValueError("Nota no encontrada")
        dest = Path(dest)
        if dest.suffix.lower() != ".cnote":
            dest = dest.with_suffix(".cnote")
        payload = {
            "v": 1,
            "app": "CryptoBro",
            "format": "cnote",
            "title": msg.title,
            "folder": msg.folder or "",
            "content_encrypted": msg.content_encrypted,
        }
        dest.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(dest)

    def export_notes_folder(self, folder: str, dest: str) -> str:
        """Exporta todas las notas de un grupo a .cbnotes (JSON array)."""
        import json
        from pathlib import Path

        folder = folder or ""
        notes = [m for m in self.get_all_messages() if (m.folder or "") == folder]
        group = self.get_note_group(folder) if folder else None
        dest = Path(dest)
        if dest.suffix.lower() != ".cbnotes":
            dest = dest.with_suffix(".cbnotes")
        payload = {
            "v": 1,
            "app": "CryptoBro",
            "format": "cbnotes",
            "folder": folder,
            "description": (group.description if group else "") or "",
            "notes": [
                {
                    "title": m.title,
                    "folder": m.folder or "",
                    "content_encrypted": m.content_encrypted,
                }
                for m in notes
            ],
        }
        dest.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(dest)

    def import_note(self, src: str) -> int:
        """Importa .cnote o .cbnotes (devuelve id de la primera / única nota)."""
        import json
        from pathlib import Path

        src = Path(src)
        if not src.is_file():
            raise FileNotFoundError("Archivo no encontrado")
        data = json.loads(src.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Formato de nota inválido")

        if data.get("format") == "cbnotes" or data.get("notes"):
            notes = data.get("notes") or []
            default_folder = (data.get("folder") or "").strip()
            desc = data.get("description") or ""
            if default_folder:
                self.crypto_bro.upsertNoteGroup(default_folder, desc)
            first_id = None
            for n in notes:
                folder = n.get("folder") if n.get("folder") is not None else default_folder
                folder = folder or ""
                if folder:
                    self.crypto_bro.upsertNoteGroup(folder)
                mid = self.crypto_bro.saveMessage(
                    n.get("title") or "importada",
                    n["content_encrypted"],
                    folder=folder,
                )
                if first_id is None:
                    first_id = mid
            if first_id is None and default_folder:
                return 0  # grupo vacío importado
            if first_id is None:
                raise ValueError("El archivo no trae notas")
            return first_id

        if data.get("format") == "cnote" or data.get("content_encrypted"):
            folder = data.get("folder") or ""
            if folder:
                self.crypto_bro.upsertNoteGroup(folder)
            return self.crypto_bro.saveMessage(
                data.get("title") or "importada",
                data["content_encrypted"],
                folder=folder,
            )
        raise ValueError("Formato de nota inválido")

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
        progress=None,
    ) -> tuple:
        """
        Complementarios (offline):
        - bloqueo = calendario hasta unlock_at (años/días/horas/min).
        - descifrado = puzzle CPU (min/seg) al Resolver, tras vencer el bloqueo.
        - password opcional: tras calendario/puzzle pide contraseña para abrir el .sbro.
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
        from domain.paths import capsule_dir

        store = str(capsule_dir(self.vault.name))
        extension, used_key, bros_path = self.encryptFile(
            file_path,
            key,
            generated=True,
            out_ext=".sbro",
            out_dir=store,
            progress=progress,
        )
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
            raise FileNotFoundError(f"No está el archivo de cápsula: {cap.bros_path}")

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
        """Lista .bros de cifrado normal. Excluye .sbro y rutas de cápsulas."""
        from pathlib import Path

        from domain.cryptoBro import read_bros_name
        from domain.paths import cipher_dir

        cap_paths = {
            os.path.abspath(c.bros_path)
            for c in self.get_all_capsules()
            if c.bros_path
        }
        items = []
        d = Path(cipher_dir())
        # solo .bros (cápsulas nuevas = .sbro)
        for p in sorted(d.glob("*.bros")):
            if not p.is_file():
                continue
            if os.path.abspath(str(p)) in cap_paths:
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
        """Exporta cápsula portátil .sbro (meta + payload; ZIP_STORED, sin cargar todo en RAM)."""
        import zipfile
        from pathlib import Path

        from domain.cryptoBro import _CHUNK_SIZE

        cap = self.crypto_bro.getCapsuleById(capsule_id)
        if not cap:
            raise ValueError("Cápsula no encontrada")
        src = Path(cap.bros_path)
        if not src.is_file():
            raise FileNotFoundError(f"No está el archivo de cápsula: {cap.bros_path}")
        dest = Path(dest)
        # .sbro portátil (aceptamos .cap legado al importar)
        if dest.suffix.lower() not in (".sbro", ".cap"):
            dest = dest.with_suffix(".sbro")

        h = hashlib.sha256()
        with open(src, "rb") as f:
            while True:
                chunk = f.read(_CHUNK_SIZE)
                if not chunk:
                    break
                h.update(chunk)
        meta = {
            "v": 3,
            "app": "CryptoBro",
            "format": "sbro",
            "label": cap.label,
            "unlock_at": cap.unlock_at,
            "extension": cap.extension,
            "key": cap.key,
            "created": datetime.now().isoformat(timespec="seconds"),
            "sha256": h.hexdigest(),
            "payload": "payload.bin",
        }
        with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_STORED) as zf:
            zf.writestr("capsule.json", json.dumps(meta, indent=2))
            zf.write(src, arcname="payload.bin")
        return str(dest)

    def import_capsule(self, src: str) -> int:
        """Importa .sbro (o .cap legado) al almacén privado de la bóveda."""
        import zipfile
        from pathlib import Path

        from domain.cryptoBro import _CHUNK_SIZE
        from domain.paths import capsule_dir

        src = Path(src)
        if not src.is_file():
            raise FileNotFoundError("Archivo no encontrado")
        d = capsule_dir(self.vault.name)
        sbro_path = d / (secrets.token_hex(16) + ".sbro")

        try:
            with zipfile.ZipFile(src, "r") as zf:
                meta = json.loads(zf.read("capsule.json"))
                names = set(zf.namelist())
                for candidate in ("payload.bin", "payload.sbro", "payload.bros"):
                    if candidate in names:
                        payload_name = candidate
                        break
                else:
                    raise ValueError("Copia de cápsula inválida (.sbro)")
                h = hashlib.sha256()
                with zf.open(payload_name) as src_f, open(sbro_path, "wb") as dst:
                    while True:
                        chunk = src_f.read(_CHUNK_SIZE)
                        if not chunk:
                            break
                        h.update(chunk)
                        dst.write(chunk)
        except ValueError:
            sbro_path.unlink(missing_ok=True)
            raise
        except Exception as e:
            sbro_path.unlink(missing_ok=True)
            raise ValueError("Copia de cápsula inválida (.sbro)") from e

        if meta.get("sha256") and h.hexdigest() != meta["sha256"]:
            sbro_path.unlink(missing_ok=True)
            raise ValueError("Integridad fallida: el .sbro está corrupto o alterado")
        if not meta.get("key"):
            sbro_path.unlink(missing_ok=True)
            raise ValueError("La cápsula no trae clave")

        cid = self.crypto_bro.addCapsule(
            meta.get("label", "importada"),
            str(sbro_path),
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
