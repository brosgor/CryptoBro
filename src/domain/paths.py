"""Rutas absolutas del proyecto (no dependen del CWD)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
DATA = ROOT / "data"
ASSETS = SRC / "assets"
WORDS_JSON = ASSETS / "words.json"
ICON_PNG = ASSETS / "images" / "favicon.png"

VAULTS_DIR = DATA / "vaults"
ACTIVE_VAULT_FILE = DATA / "active_vault.txt"
DB_WORK = DATA / "secure.db.work"  # plaintext solo mientras la app está abierta
VAULT_SESSION = DATA / "vault.session"


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


def vault_dir(name: str) -> Path:
    return VAULTS_DIR / sanitize_vault_name(name)


def vault_meta_path(name: str) -> Path:
    return vault_dir(name) / "vault.meta"


def vault_enc_path(name: str) -> Path:
    return vault_dir(name) / "secure.db.enc"


def list_vault_names() -> list[str]:
    ensure_data_dir()
    if not VAULTS_DIR.exists():
        return []
    names = []
    for p in sorted(VAULTS_DIR.iterdir()):
        if p.is_dir() and (p / "vault.meta").exists() and (p / "secure.db.enc").exists():
            names.append(p.name)
    return names


def get_active_vault_name() -> str | None:
    if ACTIVE_VAULT_FILE.exists():
        n = ACTIVE_VAULT_FILE.read_text(encoding="utf-8").strip()
        if n:
            return n
    names = list_vault_names()
    return names[0] if names else None


def set_active_vault_name(name: str) -> None:
    ensure_data_dir()
    ACTIVE_VAULT_FILE.write_text(sanitize_vault_name(name), encoding="utf-8")


def migrate_legacy_vault() -> None:
    """Mueve data/vault.meta + secure.db.enc → data/vaults/default/."""
    ensure_data_dir()
    legacy_meta = DATA / "vault.meta"
    legacy_enc = DATA / "secure.db.enc"
    if not legacy_meta.exists() or not legacy_enc.exists():
        return
    dest = vault_dir("default")
    if (dest / "vault.meta").exists():
        return
    dest.mkdir(parents=True, exist_ok=True)
    legacy_meta.replace(dest / "vault.meta")
    legacy_enc.replace(dest / "secure.db.enc")
    set_active_vault_name("default")
