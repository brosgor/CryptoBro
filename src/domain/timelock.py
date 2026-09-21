"""Time-lock puzzle offline (RSW-style): squarings secuenciales mod n.

Creación rápida con trampa RSA (se descarta). Desbloqueo ≈ duración estimada de CPU.
No usa reloj ni red. CPU más rápida = desbloquea antes (límite inherente del TLP).

Capa opcional: envolver la clave con contraseña (PBKDF2 + Fernet) tras el puzzle.
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
import time
from typing import Callable, Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

_PW_KIND = "pw"
_PBKDF2_ITERS = 200_000


def _benchmark_squarings(n: int, sample_ms: float = 80.0) -> float:
    a = secrets.randbelow(n - 3) + 2
    count = 0
    t0 = time.perf_counter()
    while (time.perf_counter() - t0) * 1000 < sample_ms:
        a = pow(a, 2, n)
        count += 1
    elapsed = time.perf_counter() - t0
    return max(count / elapsed, 1.0)


def wrap_key_with_password(plaintext_key: str, password: str) -> str:
    """Envuelve la clave del .bros con una contraseña (opcional en cápsulas)."""
    if len(password) < 8:
        raise ValueError("La contraseña de la cápsula debe tener al menos 8 caracteres")
    salt = secrets.token_bytes(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_PBKDF2_ITERS,
    )
    fkey = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
    wrapped = Fernet(fkey).encrypt(plaintext_key.encode("utf-8")).decode("ascii")
    return json.dumps(
        {"v": 1, "kind": _PW_KIND, "salt": salt.hex(), "wrap": wrapped},
        separators=(",", ":"),
    )


def is_password_wrap(blob: str) -> bool:
    if not blob or blob[0] != "{":
        return False
    try:
        data = json.loads(blob)
        return data.get("v") == 1 and data.get("kind") == _PW_KIND and "wrap" in data
    except Exception:
        return False


def unwrap_key_with_password(blob: str, password: str) -> str:
    data = json.loads(blob) if isinstance(blob, str) else blob
    if data.get("kind") != _PW_KIND:
        raise ValueError("No es un envoltorio de contraseña")
    salt = bytes.fromhex(data["salt"])
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_PBKDF2_ITERS,
    )
    fkey = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
    try:
        return Fernet(fkey).decrypt(data["wrap"].encode("ascii")).decode("utf-8")
    except InvalidToken as e:
        raise ValueError("Contraseña incorrecta") from e


def seal(plaintext_key: str, duration_seconds: float, password_protected: bool = False) -> dict:
    """Envuelve la clave en un puzzle. duration_seconds → T squarings (estimado)."""
    if duration_seconds <= 0:
        raise ValueError("Duración debe ser > 0")

    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    nums = private.private_numbers()
    n = nums.public_numbers.n
    p, q = nums.p, nums.q
    phi = (p - 1) * (q - 1)

    rate = _benchmark_squarings(n)
    t_steps = max(1, int(rate * duration_seconds))

    a0 = secrets.randbelow(n - 3) + 2
    # a0^(2^T) mod n sin hacer T squarings (trampa φ(n)); luego se olvida p,q
    exp = pow(2, t_steps, phi)
    a_final = pow(a0, exp, n)

    digest = hashlib.sha256(a_final.to_bytes((n.bit_length() + 7) // 8, "big")).digest()
    fkey = base64.urlsafe_b64encode(digest)
    wrapped = Fernet(fkey).encrypt(plaintext_key.encode("utf-8")).decode("ascii")

    # no guardar p, q, phi
    out = {
        "v": 1,
        "n": str(n),
        "a": str(a0),
        "t": t_steps,
        "wrap": wrapped,
        "secs": int(duration_seconds),
        "rate": int(rate),
    }
    if password_protected:
        out["pw"] = 1
    return out


def seal_to_str(
    plaintext_key: str, duration_seconds: float, password_protected: bool = False
) -> str:
    return json.dumps(
        seal(plaintext_key, duration_seconds, password_protected=password_protected),
        separators=(",", ":"),
    )


def is_puzzle(blob: str) -> bool:
    if not blob or blob[0] != "{":
        return False
    try:
        data = json.loads(blob)
        return (
            data.get("v") == 1
            and "wrap" in data
            and "t" in data
            and data.get("kind") != _PW_KIND
        )
    except Exception:
        return False


def needs_password(blob: str) -> bool:
    """True si al abrir (tras puzzle/calendario) hace falta contraseña."""
    if is_password_wrap(blob):
        return True
    if is_puzzle(blob):
        try:
            return bool(json.loads(blob).get("pw"))
        except Exception:
            return False
    return False


def open_puzzle(
    blob: str,
    progress: Optional[Callable[[int, int], None]] = None,
) -> str:
    """Resuelve squarings y devuelve la clave (o envoltorio pw) en claro. progress(done, total)."""
    data = json.loads(blob) if isinstance(blob, str) else blob
    n = int(data["n"])
    a = int(data["a"])
    t_steps = int(data["t"])
    wrapped = data["wrap"].encode("ascii")

    # progreso por tiempo (no cada %): evita inundar la UI
    last_report = 0.0
    for i in range(t_steps):
        a = pow(a, 2, n)
        if progress:
            now = time.perf_counter()
            if i + 1 == t_steps or now - last_report >= 0.15:
                progress(i + 1, t_steps)
                last_report = now

    digest = hashlib.sha256(a.to_bytes((n.bit_length() + 7) // 8, "big")).digest()
    fkey = base64.urlsafe_b64encode(digest)
    return Fernet(fkey).decrypt(wrapped).decode("utf-8")
