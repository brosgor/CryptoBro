from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Tuple

@dataclass
class SecureMessage:
    title: str
    content_encrypted: str
    id: Optional[int] = None

    def to_json(self) -> Dict[str, Any]:
        """Retorna un diccionario serializable a JSON."""
        return asdict(self)

    @classmethod
    def from_db(cls, row: Tuple) -> 'SecureMessage':
        """Crea una instancia a partir de una tupla de la base de datos."""
        # row: (id, title, content_encrypted)
        return cls(id=row[0], title=row[1], content_encrypted=row[2])
