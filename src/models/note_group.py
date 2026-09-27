from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, Tuple


@dataclass
class NoteGroup:
    title: str
    description: str = ""
    id: Optional[int] = None

    def to_json(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_db(cls, row: Tuple) -> "NoteGroup":
        # row: (id, title, description)
        return cls(id=row[0], title=row[1] or "", description=row[2] or "")
