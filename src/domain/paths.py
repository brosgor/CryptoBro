"""
Rutas portables (AppImage / .exe / desarrollo).

- Por defecto: misma carpeta del binario (o raíz del repo en dev).
- Al crear/importar una bóveda se fija el WORKSPACE (carpeta de esa bóveda).
- Estructura del workspace:
    <workspace>/
      <nombre>.gor
      data/archivos_cifrados/
      data/archivos_descifrados/

Override: CRYPTOBRO_HOME=/ruta/portable
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

APP_NAME = "CryptoBro"

GOR_META = "vault.meta"
GOR_ENC = "secure.db.enc"
GOR_INFO = "backup.json"


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False)) or hasattr(sys, "_MEIPASS")


def binary_dir() -> Path:
    """Carpeta del ejecutable (AppImage/exe) o del proyecto en desarrollo."""
    override = os.environ.get("CRYPTOBRO_HOME", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    # AppImage: carpeta del .AppImage (escribible); si no, ~/CryptoBro
    appimage = os.environ.get("APPIMAGE", "").strip()
    if appimage:
        parent = Path(appimage).resolve().parent
        try:
            parent.mkdir(parents=True, exist_ok=True)
            test = parent / ".cryptobro-write-test"
            test.write_text("ok", encoding="utf-8")
            test.unlink(missing_ok=True)
            return parent
        except OSError:
            home = Path.home() / "CryptoBro"
            home.mkdir(parents=True, exist_ok=True)
            return home
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    # desarrollo: raíz del repo
    return Path(__file__).resolve().parents[2]


def resource_dir() -> Path:
    """Recursos empaquetados (icono, words)."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[1]


SRC = resource_dir()
ASSETS = SRC / "assets"
WORDS_JSON = ASSETS / "words.json"
ICON_PNG = ASSETS / "images" / "favicon.png"

# Estado del workspace activo (junto al binario)
_HOME = binary_dir()
_WORKSPACE_FILE = _HOME / "cryptobro-workspace.txt"
_REGISTRY_FILE = _HOME / "cryptobro-vaults.json"


def get_workspace() -> Path:
    if _WORKSPACE_FILE.exists():
        raw = _WORKSPACE_FILE.read_text(encoding="utf-8").strip()
        if raw:
            p = Path(raw).expanduser()
            if p.is_dir():
                return p.resolve()
    return _HOME.resolve()


def set_workspace(path: Path) -> None:
    path = Path(path).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    _WORKSPACE_FILE.write_text(str(path), encoding="utf-8")
    ensure_workspace_layout(path)


def ensure_workspace_layout(workspace: Path | None = None) -> Path:
    ws = Path(workspace) if workspace else get_workspace()
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "data" / "archivos_cifrados").mkdir(parents=True, exist_ok=True)
    (ws / "data" / "archivos_descifrados").mkdir(parents=True, exist_ok=True)
    return ws


def cipher_dir(workspace: Path | None = None) -> Path:
    return ensure_workspace_layout(workspace) / "data" / "archivos_cifrados"


def plain_dir(workspace: Path | None = None) -> Path:
    return ensure_workspace_layout(workspace) / "data" / "archivos_descifrados"


# Compat: DATA se actualiza en ensure_data_dir()
def refresh_data_paths() -> None:
    """No-op; ensure_data_dir actualiza los globals."""
    pass


def db_work() -> Path:
    return ensure_workspace_layout() / "secure.db.work"


def vault_session() -> Path:
    return ensure_workspace_layout() / "vault.session"


DATA = _HOME
VAULTS_DIR = _HOME
ACTIVE_VAULT_FILE = _HOME / "active_vault.txt"
DB_WORK = _HOME / "secure.db.work"
VAULT_SESSION = _HOME / "vault.session"


def ensure_data_dir() -> None:
    """Inicializa workspace por defecto (junto al binario) y migra legado."""
    global DATA, VAULTS_DIR, ACTIVE_VAULT_FILE, DB_WORK, VAULT_SESSION
    ws = ensure_workspace_layout()
    DATA = ws
    VAULTS_DIR = ws  # los .gor viven en el workspace (raíz)
    ACTIVE_VAULT_FILE = ws / "active_vault.txt"
    DB_WORK = ws / "secure.db.work"
    VAULT_SESSION = ws / "vault.session"
    migrate_all_legacy()


def sanitize_vault_name(name: str) -> str:
    name = (name or "").strip()
    name = re.sub(r"[^\w\-áéíóúñÁÉÍÓÚÑ ]+", "", name, flags=re.UNICODE)
    name = re.sub(r"\s+", "-", name).strip("-_")
    if not name:
        raise ValueError("Nombre de bóveda vacío")
    if len(name) > 64:
        name = name[:64]
    return name.lower()


def vault_gor_path(name: str, workspace: Path | None = None) -> Path:
    ws = ensure_workspace_layout(workspace)
    return ws / f"{sanitize_vault_name(name)}.gor"


def _load_registry() -> list[str]:
    if not _REGISTRY_FILE.exists():
        return []
    try:
        data = json.loads(_REGISTRY_FILE.read_text(encoding="utf-8"))
        return [str(p) for p in data.get("vaults", [])]
    except (json.JSONDecodeError, OSError):
        return []


def _save_registry(paths: list[str]) -> None:
    _HOME.mkdir(parents=True, exist_ok=True)
    uniq = []
    for p in paths:
        rp = str(Path(p).resolve())
        if rp not in uniq and Path(rp).exists():
            uniq.append(rp)
    _REGISTRY_FILE.write_text(
        json.dumps({"vaults": uniq}, indent=2), encoding="utf-8"
    )


def register_vault_path(gor_path: Path) -> None:
    gor_path = Path(gor_path).resolve()
    paths = _load_registry()
    s = str(gor_path)
    if s not in paths:
        paths.append(s)
    _save_registry(paths)
    set_workspace(gor_path.parent)


def unregister_vault_path(gor_path: Path) -> None:
    s = str(Path(gor_path).resolve())
    _save_registry([p for p in _load_registry() if p != s])


def list_vault_entries() -> list[tuple[str, Path]]:
    """[(nombre, path_al_gor), ...] del workspace actual + registro."""
    ensure_data_dir()
    found: dict[str, Path] = {}
    ws = get_workspace()
    for p in sorted(ws.glob("*.gor")):
        if p.is_file():
            found[p.stem] = p.resolve()
            register_vault_path(p)
    for raw in _load_registry():
        p = Path(raw)
        if p.is_file() and p.suffix.lower() == ".gor":
            found[p.stem] = p.resolve()
    return sorted(found.items(), key=lambda x: x[0])


def list_vault_names() -> list[str]:
    return [n for n, _ in list_vault_entries()]


def resolve_vault_gor(name: str) -> Path | None:
    name = sanitize_vault_name(name)
    for n, p in list_vault_entries():
        if n == name:
            return p
    # fallback: workspace actual
    p = vault_gor_path(name)
    return p if p.exists() else None


def get_active_vault_name() -> str | None:
    ensure_data_dir()
    if ACTIVE_VAULT_FILE.exists():
        n = ACTIVE_VAULT_FILE.read_text(encoding="utf-8").strip()
        if n and resolve_vault_gor(n):
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
                    "app": APP_NAME,
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


def migrate_all_legacy() -> None:
    """Migra data/ del repo o layouts viejos al workspace portable."""
    ws = ensure_workspace_layout()

    # repo data/vaults/*.gor → workspace
    repo_data = binary_dir() / "data"
    if not _is_frozen():
        repo_data = Path(__file__).resolve().parents[2] / "data"
    old_vaults = repo_data / "vaults"
    if old_vaults.exists():
        for p in old_vaults.glob("*.gor"):
            dest = ws / p.name
            if not dest.exists():
                shutil.copy2(p, dest)
                register_vault_path(dest)
        for d in old_vaults.iterdir():
            if d.is_dir() and (d / "vault.meta").exists() and (d / "secure.db.enc").exists():
                dest = ws / f"{d.name}.gor"
                if not dest.exists():
                    write_gor(
                        dest,
                        (d / "vault.meta").read_text(encoding="utf-8"),
                        (d / "secure.db.enc").read_bytes(),
                        d.name,
                    )
                    register_vault_path(dest)

    # dos archivos sueltos en workspace o data/
    for base in (ws, repo_data):
        meta = base / "vault.meta"
        enc = base / "secure.db.enc"
        dest = ws / "default.gor"
        if meta.exists() and enc.exists() and not dest.exists():
            write_gor(dest, meta.read_text(encoding="utf-8"), enc.read_bytes(), "default")
            register_vault_path(dest)
            meta.unlink(missing_ok=True)
            enc.unlink(missing_ok=True)
