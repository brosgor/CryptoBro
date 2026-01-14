from dataclasses import dataclass

@dataclass
class SecureData:
    hash: str
    key: str
    extension: str
    id: int = None
