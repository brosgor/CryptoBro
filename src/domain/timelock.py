"""Time-lock puzzle offline (RSW-style): squarings secuenciales mod n.

Creación rápida con trampa RSA (se descarta). Desbloqueo ≈ duración estimada de CPU.
No usa reloj ni red. CPU más rápida = desbloquea antes (límite inherente del TLP).
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
import time
from typing import Callable, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa


def _benchmark_squarings(n: int, sample_ms: float = 80.0) -> float:
    a = secrets.randbelow(n - 3) + 2
    count = 0
    t0 = time.perf_counter()
    while (time.perf_counter() - t0) * 1000 < sample_ms:
        a = pow(a, 2, n)
        count += 1
    elapsed = time.perf_counter() - t0
    return max(count / elapsed, 1.0)


def seal(plaintext_key: str, duration_seconds: float) -> dict:
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
    return {
        "v": 1,
        "n": str(n),
        "a": str(a0),
        "t": t_steps,
        "wrap": wrapped,
        "secs": int(duration_seconds),
        "rate": int(rate),
    }


def seal_to_str(plaintext_key: str, duration_seconds: float) -> str:
    return json.dumps(seal(plaintext_key, duration_seconds), separators=(",", ":"))


def is_puzzle(blob: str) -> bool:
    if not blob or blob[0] != "{":
        return False
    try:
        data = json.loads(blob)
        return data.get("v") == 1 and "wrap" in data and "t" in data
    except Exception:
        return False


def open_puzzle(
    blob: str,
    progress: Optional[Callable[[int, int], None]] = None,
) -> str:
    """Resuelve squarings y devuelve la clave en claro. progress(done, total)."""
    data = json.loads(blob) if isinstance(blob, str) else blob
    n = int(data["n"])
    a = int(data["a"])
    t_steps = int(data["t"])
    wrapped = data["wrap"].encode("ascii")

    report_every = max(1, t_steps // 100)
    for i in range(t_steps):
        a = pow(a, 2, n)
        if progress and (i % report_every == 0 or i + 1 == t_steps):
            progress(i + 1, t_steps)

    digest = hashlib.sha256(a.to_bytes((n.bit_length() + 7) // 8, "big")).digest()
    fkey = base64.urlsafe_b64encode(digest)
    return Fernet(fkey).decrypt(wrapped).decode("utf-8")
