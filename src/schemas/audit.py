"""Schemas for the argument auditor."""

from typing import Literal

from pydantic import BaseModel, Field


class AuditFinding(BaseModel):
    """A single violation of the structural conditions, with a revision pointer."""
    condition: Literal["connectivity", "conclusion", "integrity", "circular"] = Field(
        description="Violated condition",
    )
    step_symbols: list[str] = Field(description="Symbols of the affected steps")
    issue: str = Field(description="What is wrong")
    pointer: str = Field(
        description="How to revise the argument to fix it (never a rewritten proposition)"
    )


class AuditResult(BaseModel):
    """Outcome of auditing an argument against the structural conditions."""
    satisfied: bool
    findings: list[AuditFinding]
