"""
Step schema for argument components.
This defines the data structure for individual steps in arguments and assumptions.
"""

from pydantic import BaseModel


class Formalization(BaseModel):
    """Formal logic representation of a proposition"""
    ascii: str
    json: dict | None = None


class Step(BaseModel):
    """Steps in arguments or assumptions"""
    symbol: str
    proposition: str
    justifiers: list[str]
    truth: str
    valid: str  # Keep for backward compatibility
    # New attributes for rearchitecture
    valid_content: str | None = None  # Validity from content evaluation
    valid_formal: str | None = None   # Validity from formal evaluation  
    formalization: Formalization | None = None  # Formal logic representation
