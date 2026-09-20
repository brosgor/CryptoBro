"""Bóveda multi-perfil: un archivo .gor por bóveda (meta + db cifrada)."""
from __future__ import annotations

import atexit
import json
import os
import signal
import sqlite3
import zipfile
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from domain import paths as P
from domain.paths import (
    ensure_data_dir,
    get_active_vault_name,
    list_vault_names,
    read_gor_parts,
    register_vault_path,
    resolve_vault_gor,
    sanitize_vault_name,
    set_active_vault_name,
    set_workspace,
    unregister_vault_path,
    vault_gor_path,
    write_gor,
)

_VERIFIER = b"cryptobro-vault-v1"
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1

_ACTIVE: "Vault | None" = None


def _shutdown_vault() -> None:
    global _ACTIVE
    if _ACTIVE is not None:
        try:
            _ACTIVE.lock()
        except Exception:
            pass
        _ACTIVE = None


def _on_signal(signum, frame) -> None:
    _shutdown_vault()
    raise SystemExit(128 + (signum if isinstance(signum, int) else 0))


class VaultError(Exception):
    pass


class Vault:
    """Bóveda = <workspace>/<nombre>.gor (portable)."""

    def __init__(self, name: str | None = None) -> None:
        ensure_data_dir()
        if name:
            self.name = sanitize_vault_name(name)
        else:
            self.name = get_active_vault_name() or "default"
        self._fernet: Fernet | None = None
        self._plain_path: Path | None = None
        self._meta_json: dict | None = None
        self._locked = True

    @property
    def gor_path(self) -> Path:
        found = resolve_vault_gor(self.name)
        return found if found else vault_gor_path(self.name)

    @property
    def is_setup(self) -> bool:
        return self.gor_path.exists()

    @property
    def any_vault_exists(self) -> bool:
        return bool(list_vault_names())

    @property
    def db_path(self) -> str:
        if not self._plain_path:
            raise VaultError("Bóveda bloqueada")
        return str(self._plain_path)

    def select(self, name: str) -> None:
        if not self._locked:
            raise VaultError("Bloquea la bóveda actual antes de cambiar")
        self.name = sanitize_vault_name(name)
        found = resolve_vault_gor(self.name)
        if found:
            set_workspace(found.parent)
            register_vault_path(found)
        set_active_vault_name(self.name)

    def _derive(self, password: str, salt: bytes) -> bytes:
        kdf = Scrypt(salt=salt, length=32, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P)
        return kdf.derive(password.encode("utf-8"))

    def _fernet_from_key_material(self, key_material: bytes) -> Fernet:
        import base64

        return Fernet(base64.urlsafe_b64encode(key_material))

    @staticmethod
    def _shred(path: Path) -> None:
        if not path.exists():
            return
        try:
            size = path.stat().st_size
            with open(path, "wb") as f:
                f.write(os.urandom(max(size, 1)))
                f.flush()
                os.fsync(f.fileno())
        except OSError:
            pass
        path.unlink(missing_ok=True)

    def _write_session(self) -> None:
        P.VAULT_SESSION.write_text(
            json.dumps(
                {"work": str(P.DB_WORK), "pid": os.getpid(), "vault": self.name}
            ),
            encoding="utf-8",
        )

    def _clear_session(self) -> None:
        P.VAULT_SESSION.unlink(missing_ok=True)

    def _recover_orphan_if_any(self, fernet: Fernet) -> None:
        if not P.DB_WORK.exists():
            self._clear_session()
            return
        try:
            enc = fernet.encrypt(P.DB_WORK.read_bytes())
            meta_text = json.dumps(self._meta_json or {})
            # si no hay meta en memoria, leer del .gor
            if self.gor_path.exists() and not self._meta_json:
                meta_text, _ = read_gor_parts(self.gor_path)
            elif self._meta_json:
                meta_text = json.dumps(self._meta_json)
            write_gor(self.gor_path, meta_text, enc, self.name)
        except Exception:
            pass
        self._shred(P.DB_WORK)
        self._clear_session()

    def _load_meta(self) -> dict:
        meta_text, _ = read_gor_parts(self.gor_path)
        return json.loads(meta_text)

    def setup(self, password: str, name: str | None = None) -> None:
        if name:
            self.select(name)
        if len(password) < 8:
            raise VaultError("La clave debe tener al menos 8 caracteres")
        if self.is_setup:
            raise VaultError(f"La bóveda '{self.name}' ya existe")
        ensure_data_dir()
        salt = os.urandom(16)
        fernet = self._fernet_from_key_material(self._derive(password, salt))
        verifier = fernet.encrypt(_VERIFIER).decode("ascii")
        meta = {"v": 1, "salt": salt.hex(), "verifier": verifier, "name": self.name}
        tmp = P.DATA / f"_init_{self.name}.db"
        conn = sqlite3.connect(tmp)
        conn.close()
        enc = fernet.encrypt(tmp.read_bytes())
        tmp.unlink(missing_ok=True)
        path = vault_gor_path(self.name)
        write_gor(path, json.dumps(meta), enc, self.name)
        register_vault_path(path)
        from domain.paths import unhide_vault_path

        unhide_vault_path(path)
        set_workspace(path.parent)
        set_active_vault_name(self.name)
        self.unlock(password)

    def unlock(self, password: str) -> None:
        if not self.gor_path.exists():
            raise VaultError(f"La bóveda '{self.name}' no existe")
        meta_text, enc_bytes = read_gor_parts(self.gor_path)
        meta = json.loads(meta_text)
        salt = bytes.fromhex(meta["salt"])
        fernet = self._fernet_from_key_material(self._derive(password, salt))
        try:
            if fernet.decrypt(meta["verifier"].encode("ascii")) != _VERIFIER:
                raise VaultError("Clave de bloqueo incorrecta")
        except InvalidToken as e:
            raise VaultError("Clave de bloqueo incorrecta") from e

        self._fernet = fernet
        self._meta_json = meta
        self._recover_orphan_if_any(fernet)
        # re-read after possible recovery
        if self.gor_path.exists():
            _, enc_bytes = read_gor_parts(self.gor_path)

        plain = fernet.decrypt(enc_bytes)
        P.DB_WORK.write_bytes(plain)
        self._plain_path = P.DB_WORK
        self._write_session()
        self._locked = False
        set_active_vault_name(self.name)
        self._register_shutdown_hooks()

        legacy = P.DATA / "secure.db"
        if legacy.exists() and legacy.stat().st_size > 0:
            try:
                self._merge_legacy(legacy)
            except Exception:
                pass

    def change_password(self, old_password: str, new_password: str) -> None:
        if self._locked or not self._fernet or not self._plain_path:
            raise VaultError("Desbloquea la bóveda primero")
        if len(new_password) < 8:
            raise VaultError("La nueva clave debe tener al menos 8 caracteres")
        meta = self._meta_json or self._load_meta()
        salt_old = bytes.fromhex(meta["salt"])
        try:
            old_f = self._fernet_from_key_material(self._derive(old_password, salt_old))
            if old_f.decrypt(meta["verifier"].encode("ascii")) != _VERIFIER:
                raise VaultError("Clave actual incorrecta")
        except InvalidToken as e:
            raise VaultError("Clave actual incorrecta") from e

        salt = os.urandom(16)
        new_f = self._fernet_from_key_material(self._derive(new_password, salt))
        verifier = new_f.encrypt(_VERIFIER).decode("ascii")
        self._meta_json = {
            "v": 1,
            "salt": salt.hex(),
            "verifier": verifier,
            "name": self.name,
        }
        self._fernet = new_f
        self.flush()

    def delete_vault(
        self,
        name: str | None = None,
        confirm_password: str | None = None,
        wipe_file: bool = True,
    ) -> None:
        """
        wipe_file=True  → borra el .gor del disco.
        wipe_file=False → solo quita de la lista (el archivo permanece).
        """
        from domain.paths import hide_vault_path, unhide_vault_path

        target = sanitize_vault_name(name or self.name)
        if not self._locked and target == self.name:
            raise VaultError("Bloquea la bóveda antes de eliminarla")
        path = resolve_vault_gor(target) or vault_gor_path(target)
        if wipe_file:
            if not path.exists():
                raise VaultError("La bóveda no existe")
            self._shred(path)
            unregister_vault_path(path)
            unhide_vault_path(path)
        else:
            if path.exists():
                hide_vault_path(path)
            else:
                raise VaultError("La bóveda no existe")
        if get_active_vault_name() == target:
            names = list_vault_names()
            if names:
                set_active_vault_name(names[0])
            else:
                P.ACTIVE_VAULT_FILE.unlink(missing_ok=True)

    def reset_contents(self, password: str) -> None:
        if self._locked or not self._plain_path:
            raise VaultError("Desbloquea primero")
        meta = self._meta_json or self._load_meta()
        salt = bytes.fromhex(meta["salt"])
        try:
            f = self._fernet_from_key_material(self._derive(password, salt))
            if f.decrypt(meta["verifier"].encode("ascii")) != _VERIFIER:
                raise VaultError("Clave incorrecta")
        except InvalidToken as e:
            raise VaultError("Clave incorrecta") from e

        tmp = P.DATA / f"_reset_{self.name}.db"
        conn = sqlite3.connect(tmp)
        conn.close()
        self._plain_path.write_bytes(tmp.read_bytes())
        tmp.unlink(missing_ok=True)
        self.flush()

    def _register_shutdown_hooks(self) -> None:
        global _ACTIVE
        _ACTIVE = self
        atexit.register(_shutdown_vault)
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, _on_signal)
            except (ValueError, OSError):
                pass

    def lock(self) -> None:
        if self._locked:
            return
        if self._fernet and self._plain_path and self._plain_path.exists():
            try:
                self.flush()
            except Exception:
                pass
            self._shred(self._plain_path)
        self._plain_path = None
        self._fernet = None
        self._meta_json = None
        self._clear_session()
        self._locked = True
        global _ACTIVE
        if _ACTIVE is self:
            _ACTIVE = None

    def flush(self) -> None:
        if self._fernet and self._plain_path and self._plain_path.exists() and self._meta_json:
            enc = self._fernet.encrypt(self._plain_path.read_bytes())
            write_gor(self.gor_path, json.dumps(self._meta_json), enc, self.name)

    def export_backup(self, dest: str | Path) -> Path:
        dest = Path(dest)
        if self._fernet:
            self.flush()
        if not self.gor_path.exists():
            raise VaultError("No hay bóveda para exportar")
        # nativo .gor; .cbvault sigue siendo el mismo zip
        if dest.suffix.lower() not in (".gor", ".cbvault"):
            dest = dest.with_suffix(".gor")
        dest.write_bytes(self.gor_path.read_bytes())
        return dest

    def import_backup(
        self, src: str | Path, vault_name: str, overwrite: bool = False
    ) -> None:
        src = Path(src)
        if not src.exists():
            raise VaultError("Archivo de copia no encontrado")
        if not self._locked:
            raise VaultError("Bloquea la bóveda antes de restaurar")
        name = sanitize_vault_name(vault_name)
        dest = vault_gor_path(name)
        if dest.exists() and not overwrite:
            raise VaultError(f"Ya existe la bóveda '{name}'")

        # valida que sea zip con meta+enc
        try:
            meta_text, enc = read_gor_parts(src)
        except (ValueError, zipfile.BadZipFile) as e:
            raise VaultError("Copia inválida (se espera .gor o .cbvault)") from e

        if overwrite and dest.exists():
            dest.replace(dest.with_suffix(dest.suffix + ".bak"))
        write_gor(dest, meta_text, enc, name)
        register_vault_path(dest)
        from domain.paths import unhide_vault_path

        unhide_vault_path(dest)
        set_workspace(dest.parent)
        self.select(name)

    def _merge_legacy(self, legacy: Path) -> None:
        if not self._plain_path:
            return
        src = sqlite3.connect(legacy)
        dst = sqlite3.connect(self._plain_path)
        try:
            for table in ("data", "messages", "capsules"):
                try:
                    rows = src.execute(f"SELECT * FROM {table}").fetchall()
                except sqlite3.Error:
                    continue
                if not rows:
                    continue
                cols = [d[0] for d in src.execute(f"PRAGMA table_info({table})").fetchall()]
                placeholders = ",".join("?" * len(cols))
                col_list = ",".join(cols)
                for row in rows:
                    try:
                        dst.execute(
                            f"INSERT OR IGNORE INTO {table} ({col_list}) VALUES ({placeholders})",
                            row,
                        )
                    except sqlite3.Error:
                        pass
            dst.commit()
        finally:
            src.close()
            dst.close()
        legacy.rename(legacy.with_suffix(".db.bak"))
        self.flush()
