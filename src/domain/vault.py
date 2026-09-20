"""Bóveda multi-perfil: master password + BD cifrada en reposo."""
from __future__ import annotations

import atexit
import json
import os
import signal
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from domain.paths import (
    DATA,
    DB_WORK,
    VAULT_SESSION,
    ensure_data_dir,
    get_active_vault_name,
    list_vault_names,
    migrate_legacy_vault,
    sanitize_vault_name,
    set_active_vault_name,
    vault_dir,
    vault_enc_path,
    vault_meta_path,
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
    """Una bóveda nombrada bajo data/vaults/<nombre>/."""

    def __init__(self, name: str | None = None) -> None:
        ensure_data_dir()
        migrate_legacy_vault()
        if name:
            self.name = sanitize_vault_name(name)
        else:
            self.name = get_active_vault_name() or "default"
        self._fernet: Fernet | None = None
        self._plain_path: Path | None = None
        self._locked = True
        self._password_cache: str | None = None  # solo en sesión, para change_password

    @property
    def meta_path(self) -> Path:
        return vault_meta_path(self.name)

    @property
    def enc_path(self) -> Path:
        return vault_enc_path(self.name)

    @property
    def is_setup(self) -> bool:
        return self.meta_path.exists() and self.enc_path.exists()

    @property
    def any_vault_exists(self) -> bool:
        return bool(list_vault_names())

    @property
    def db_path(self) -> str:
        if not self._plain_path:
            raise VaultError("Vault locked")
        return str(self._plain_path)

    def select(self, name: str) -> None:
        if not self._locked:
            raise VaultError("Bloquea la bóveda actual antes de cambiar")
        self.name = sanitize_vault_name(name)
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
        VAULT_SESSION.write_text(
            json.dumps(
                {"work": str(DB_WORK), "pid": os.getpid(), "vault": self.name}
            ),
            encoding="utf-8",
        )

    def _clear_session(self) -> None:
        VAULT_SESSION.unlink(missing_ok=True)

    def _recover_orphan_if_any(self, fernet: Fernet) -> None:
        if not DB_WORK.exists():
            self._clear_session()
            return
        try:
            self.enc_path.write_bytes(fernet.encrypt(DB_WORK.read_bytes()))
        except Exception:
            pass
        self._shred(DB_WORK)
        self._clear_session()

    def setup(self, password: str, name: str | None = None) -> None:
        if name:
            self.select(name)
        if len(password) < 8:
            raise VaultError("La clave debe tener al menos 8 caracteres")
        if self.is_setup:
            raise VaultError(f"La bóveda '{self.name}' ya existe")
        ensure_data_dir()
        vault_dir(self.name).mkdir(parents=True, exist_ok=True)
        salt = os.urandom(16)
        fernet = self._fernet_from_key_material(self._derive(password, salt))
        verifier = fernet.encrypt(_VERIFIER).decode("ascii")
        self.meta_path.write_text(
            json.dumps({"v": 1, "salt": salt.hex(), "verifier": verifier, "name": self.name}),
            encoding="utf-8",
        )
        tmp = DATA / f"_init_{self.name}.db"
        conn = sqlite3.connect(tmp)
        conn.close()
        self._fernet = fernet
        self._encrypt_file(tmp, self.enc_path)
        tmp.unlink(missing_ok=True)
        set_active_vault_name(self.name)
        self.unlock(password)

    def unlock(self, password: str) -> None:
        if not self.meta_path.exists():
            raise VaultError(f"La bóveda '{self.name}' no existe")
        meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
        salt = bytes.fromhex(meta["salt"])
        fernet = self._fernet_from_key_material(self._derive(password, salt))
        try:
            if fernet.decrypt(meta["verifier"].encode("ascii")) != _VERIFIER:
                raise VaultError("Clave de bloqueo incorrecta")
        except InvalidToken as e:
            raise VaultError("Clave de bloqueo incorrecta") from e

        self._fernet = fernet
        self._password_cache = password
        self._recover_orphan_if_any(fernet)

        if not self.enc_path.exists():
            raise VaultError("Falta la base cifrada de la bóveda")

        plain = fernet.decrypt(self.enc_path.read_bytes())
        DB_WORK.write_bytes(plain)
        self._plain_path = DB_WORK
        self._write_session()
        self._locked = False
        set_active_vault_name(self.name)
        self._register_shutdown_hooks()

        legacy = DATA / "secure.db"
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
        # verificar old
        meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
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
        self.meta_path.write_text(
            json.dumps({"v": 1, "salt": salt.hex(), "verifier": verifier, "name": self.name}),
            encoding="utf-8",
        )
        self._fernet = new_f
        self._password_cache = new_password
        self.flush()

    def delete_vault(self, name: str | None = None, confirm_password: str | None = None) -> None:
        """Elimina una bóveda del disco. Debe estar bloqueada si es la activa abierta."""
        target = sanitize_vault_name(name or self.name)
        if not self._locked and target == self.name:
            raise VaultError("Bloquea la bóveda antes de eliminarla")
        meta = vault_meta_path(target)
        enc = vault_enc_path(target)
        if not meta.exists():
            raise VaultError("La bóveda no existe")
        if confirm_password is not None:
            m = json.loads(meta.read_text(encoding="utf-8"))
            salt = bytes.fromhex(m["salt"])
            try:
                f = self._fernet_from_key_material(self._derive(confirm_password, salt))
                if f.decrypt(m["verifier"].encode("ascii")) != _VERIFIER:
                    raise VaultError("Clave incorrecta")
            except InvalidToken as e:
                raise VaultError("Clave incorrecta") from e
        self._shred(enc)
        self._shred(meta)
        d = vault_dir(target)
        for leftover in d.glob("*"):
            self._shred(leftover)
        try:
            d.rmdir()
        except OSError:
            pass
        if get_active_vault_name() == target:
            names = list_vault_names()
            if names:
                set_active_vault_name(names[0])
            else:
                from domain.paths import ACTIVE_VAULT_FILE

                ACTIVE_VAULT_FILE.unlink(missing_ok=True)

    def reset_contents(self, password: str) -> None:
        """Vacía datos de la bóveda (misma clave). Caller debe reiniciar el servicio."""
        if self._locked or not self._plain_path:
            raise VaultError("Desbloquea primero")
        meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
        salt = bytes.fromhex(meta["salt"])
        try:
            f = self._fernet_from_key_material(self._derive(password, salt))
            if f.decrypt(meta["verifier"].encode("ascii")) != _VERIFIER:
                raise VaultError("Clave incorrecta")
        except InvalidToken as e:
            raise VaultError("Clave incorrecta") from e

        tmp = DATA / f"_reset_{self.name}.db"
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
                self._encrypt_file(self._plain_path, self.enc_path)
            except Exception:
                pass
            self._shred(self._plain_path)
        self._plain_path = None
        self._fernet = None
        self._password_cache = None
        self._clear_session()
        self._locked = True
        global _ACTIVE
        if _ACTIVE is self:
            _ACTIVE = None

    def flush(self) -> None:
        if self._fernet and self._plain_path and self._plain_path.exists():
            self._encrypt_file(self._plain_path, self.enc_path)

    def export_backup(self, dest: str | Path) -> Path:
        dest = Path(dest)
        if self._fernet:
            self.flush()
        if not self.meta_path.exists() or not self.enc_path.exists():
            raise VaultError("No hay bóveda para exportar")
        if dest.suffix.lower() != ".cbvault":
            dest = dest.with_suffix(".cbvault")
        with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(self.meta_path, arcname="vault.meta")
            zf.write(self.enc_path, arcname="secure.db.enc")
            zf.writestr(
                "backup.json",
                json.dumps(
                    {
                        "v": 1,
                        "app": "CryptoBro",
                        "vault": self.name,
                        "created": datetime.now().isoformat(timespec="seconds"),
                    },
                    indent=2,
                ),
            )
        return dest

    def import_backup(
        self, src: str | Path, vault_name: str, overwrite: bool = False
    ) -> None:
        src = Path(src)
        if not src.exists():
            raise VaultError("Archivo de backup no encontrado")
        if not self._locked:
            raise VaultError("Bloquea la bóveda antes de restaurar")
        name = sanitize_vault_name(vault_name)
        ensure_data_dir()
        dest_dir = vault_dir(name)
        meta = vault_meta_path(name)
        enc = vault_enc_path(name)
        if (meta.exists() or enc.exists()) and not overwrite:
            raise VaultError(f"Ya existe la bóveda '{name}'")

        with zipfile.ZipFile(src, "r") as zf:
            names = set(zf.namelist())
            if "vault.meta" not in names or "secure.db.enc" not in names:
                raise VaultError("Backup inválido")
            dest_dir.mkdir(parents=True, exist_ok=True)
            if overwrite and meta.exists():
                meta.replace(meta.with_suffix(".meta.bak"))
            if overwrite and enc.exists():
                enc.replace(enc.with_suffix(".enc.bak"))
            zf.extract("vault.meta", path=dest_dir)
            zf.extract("secure.db.enc", path=dest_dir)
        self.select(name)

    def _encrypt_file(self, src: Path, dest: Path) -> None:
        assert self._fernet
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(self._fernet.encrypt(src.read_bytes()))

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
