from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class SecureCapsule:
    label: str
    bros_path: str
    key: str
    unlock_at: str  # ISO datetime UTC-ish local
    extension: str
    id: Optional[int] = None

    @classmethod
    def from_db(cls, row: Tuple) -> "SecureCapsule":
        # id, label, bros_path, key, unlock_at, extension
        return cls(
            id=row[0],
            label=row[1],
            bros_path=row[2],
            key=row[3],
            unlock_at=row[4],
            extension=row[5],
        )
