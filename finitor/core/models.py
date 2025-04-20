from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class Transaction:
    """
    Data model for a financial transaction
    """
    id: int
    amount: float
    description: str
    date: str
    currency: str
    created_at: str
    category: Optional[str] = None
    source: Optional[str] = None
    tags: List[str] = field(default_factory=list)