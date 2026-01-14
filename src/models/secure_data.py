from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Tuple

@dataclass
class SecureData:
    hash: str
    key: str
    extension: str
    id: Optional[int] = None

    def to_json(self) -> Dict[str, Any]:
        """Retorna un diccionario serializable a JSON."""
        return asdict(self)

    @classmethod
    def from_db(cls, row: Tuple) -> 'SecureData':
        """Crea una instancia a partir de una tupla de la base de datos."""
        return cls(id=row[0], hash=row[1], key=row[2], extension=row[3])
