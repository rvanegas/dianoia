"""
Pure data schemas for arguments and related structures.
These are validation-only models with minimal computed properties.
"""

from typing import List
from pydantic import BaseModel, Field
from schemas.step import Step


class Arguments(BaseModel):
    """Base arguments schema - pure data validation"""
    argument: List[Step]
    explanation: str | None = None
    file_ids: List[str] = []
    conversation_id: str | None = None  # Format: "session_uuid:conversation_id"

    def model_post_init(self, __context):
        """Simple initialization - no business logic"""
        self.explanation = None


class ArgumentsWithStep(Arguments):
    """Arguments with a specific step indicated by position"""
    index: int

    def model_post_init(self, __context):
        """Validate that indicated position exists"""
        super().model_post_init(__context)
        assert len(self.argument) > self.index


class ArgumentsWithProposition(Arguments):
    """Arguments with a proposition"""
    proposition: str


class ArgumentsWithStepAndProposition(ArgumentsWithStep, ArgumentsWithProposition):
    """Arguments with a proposition and location to make a new step"""
    pass


class ArgumentData(BaseModel):
    """Schema for argument data passed between services and agents"""
    argument: List[Step]
    file_ids: List[str] = []
