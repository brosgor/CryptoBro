"""Rutas absolutas del proyecto (no dependen del CWD)."""
from __future__ import annotations

import json
import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
DATA = ROOT / "data"
ASSETS = SRC / "assets"
WORDS_JSON = ASSETS / "words.json"
ICON_PNG = ASSETS / "images" / "favicon.png"

VAULTS_DIR = DATA / "vaults"
ACTIVE_VAULT_FILE = DATA / "active_vault.txt"
DB_WORK = DATA / "secure.db.work"
VAULT_SESSION = DATA / "vault.session"

# Contenido interno de un .gor (zip)
GOR_META = "vault.meta"
GOR_ENC = "secure.db.enc"
GOR_INFO = "backup.json"


def ensure_data_dir() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    VAULTS_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_vault_name(name: str) -> str:
    name = (name or "").strip()
    name = re.sub(r"[^\w\-áéíóúñÁÉÍÓÚÑ ]+", "", name, flags=re.UNICODE)
    name = re.sub(r"\s+", "-", name).strip("-_")
    if not name:
        raise ValueError("Nombre de bóveda vacío")
    if len(name) > 64:
        name = name[:64]
    return name.lower()


def vault_gor_path(name: str) -> Path:
    """Una bóveda = un archivo data/vaults/<nombre>.gor"""
    return VAULTS_DIR / f"{sanitize_vault_name(name)}.gor"


def list_vault_names() -> list[str]:
    ensure_data_dir()
    migrate_all_legacy()
    if not VAULTS_DIR.exists():
        return []
    names = []
    for p in sorted(VAULTS_DIR.glob("*.gor")):
        if p.is_file():
            names.append(p.stem)
    return names


def get_active_vault_name() -> str | None:
    if ACTIVE_VAULT_FILE.exists():
        n = ACTIVE_VAULT_FILE.read_text(encoding="utf-8").strip()
        if n and vault_gor_path(n).exists():
            return sanitize_vault_name(n)
    names = list_vault_names()
    return names[0] if names else None


def set_active_vault_name(name: str) -> None:
    ensure_data_dir()
    ACTIVE_VAULT_FILE.write_text(sanitize_vault_name(name), encoding="utf-8")


def write_gor(path: Path, meta_text: str, enc_bytes: bytes, vault_name: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".gor.tmp")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(GOR_META, meta_text.encode("utf-8"))
        zf.writestr(GOR_ENC, enc_bytes)
        zf.writestr(
            GOR_INFO,
            json.dumps(
                {
                    "v": 1,
                    "app": "CryptoBro",
                    "format": "gor",
                    "vault": vault_name or path.stem,
                    "created": datetime.now().isoformat(timespec="seconds"),
                },
                indent=2,
            ),
        )
    tmp.replace(path)


def read_gor_parts(path: Path) -> tuple[str, bytes]:
    with zipfile.ZipFile(path, "r") as zf:
        names = set(zf.namelist())
        if GOR_META not in names or GOR_ENC not in names:
            raise ValueError("Archivo .gor inválido")
        meta = zf.read(GOR_META).decode("utf-8")
        enc = zf.read(GOR_ENC)
    return meta, enc


def pack_dir_to_gor(dir_path: Path, dest: Path, vault_name: str) -> None:
    meta = dir_path / "vault.meta"
    enc = dir_path / "secure.db.enc"
    if not meta.exists() or not enc.exists():
        return
    write_gor(dest, meta.read_text(encoding="utf-8"), enc.read_bytes(), vault_name)


def migrate_all_legacy() -> None:
    """Convierte layouts viejos (2 archivos / carpetas) a .gor."""
    ensure_data_dir()

    # data/vault.meta + secure.db.enc → vaults/default.gor
    legacy_meta = DATA / "vault.meta"
    legacy_enc = DATA / "secure.db.enc"
    default_gor = vault_gor_path("default")
    if legacy_meta.exists() and legacy_enc.exists() and not default_gor.exists():
        write_gor(
            default_gor,
            legacy_meta.read_text(encoding="utf-8"),
            legacy_enc.read_bytes(),
            "default",
        )
        legacy_meta.unlink(missing_ok=True)
        legacy_enc.unlink(missing_ok=True)
        set_active_vault_name("default")

    # data/vaults/<name>/vault.meta+enc → data/vaults/<name>.gor
    if not VAULTS_DIR.exists():
        return
    for d in list(VAULTS_DIR.iterdir()):
        if not d.is_dir():
            continue
        gor = vault_gor_path(d.name)
        if gor.exists():
            shutil.rmtree(d, ignore_errors=True)
            continue
        meta = d / "vault.meta"
        enc = d / "secure.db.enc"
        if meta.exists() and enc.exists():
            pack_dir_to_gor(d, gor, d.name)
            shutil.rmtree(d, ignore_errors=True)
            if not ACTIVE_VAULT_FILE.exists():
                set_active_vault_name(d.name)
