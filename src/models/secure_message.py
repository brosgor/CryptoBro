from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Tuple


@dataclass
class SecureMessage:
    title: str
    content_encrypted: str
    id: Optional[int] = None
    folder: str = ""

    def to_json(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_db(cls, row: Tuple) -> "SecureMessage":
        # row: (id, title, content_encrypted[, folder])
        folder = row[3] if len(row) > 3 and row[3] is not None else ""
        return cls(
            id=row[0],
            title=row[1],
            content_encrypted=row[2],
            folder=folder,
        )
