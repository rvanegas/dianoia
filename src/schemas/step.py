"""
Step schema for argument components.
This defines the data structure for individual steps in an argument.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
import warnings


class Formalization(BaseModel):
    """Formal logic representation of a proposition"""
    model_config = ConfigDict(json_schema_serialization_defaults_required=True)
    ascii: str
    json_structure: str | None = None
    endorsed: bool = False


class Step(BaseModel):
    """A step in an argument"""
    model_config = ConfigDict(json_schema_serialization_defaults_required=True)
    symbol: str
    proposition: str
    justifiers: list[str]
    truth_score: str
    content_validity: str | None = Field(default=None, description="Content validity score from content evaluation")
    formal_validity: str | None = Field(default=None, description="Formal validity score from formal evaluation")  
    formalization: Formalization | None = None  # Formal logic representation
    

# Improvement Agent Schemas
class ExpectedConclusionImprovement(BaseModel):
    """Expected improvement in conclusion scores from a recommendation"""
    truth_score_improvement: str = Field(description="Expected improvement in truth score (e.g., '+0.4')")
    content_validity_improvement: str = Field(description="Expected improvement in content validity score (e.g., '+0.3')")
    formal_validity_improvement: str = Field(description="Expected improvement in formal validity score (e.g., '+0.2')")


class ImprovementProposition(BaseModel):
    """A proposition within an improvement recommendation"""
    # Always serialized, so published as required (schemas/api_results.py).
    model_config = ConfigDict(json_schema_serialization_defaults_required=True)
    symbol: str | None = Field(default=None, description="Symbol identifier for the proposition (e.g., '2', '3', '4'). Leave blank for new propositions.")
    proposition: str = Field(description="The natural language proposition text")
    type: Literal["new", "rewrite"] = Field(description="Type of improvement")
    original_symbol: str | None = Field(default=None, description="For rewrites, the symbol of the proposition being rewritten")
    original_proposition: str | None = Field(default=None, description="For rewrites, the original proposition text")
    justification_suggestions: list[str] = Field(description="Suggested justifications for this proposition")
    justifies_symbol: str | None = Field(default=None, description="For new propositions, the symbol of the existing proposition this new proposition justifies")


class ImprovementRecommendation(BaseModel):
    """A complete improvement recommendation set"""
    id: str = Field(description="Unique identifier for the recommendation")
    reasoning: str = Field(description="Why this improvement is suggested based on evaluation results")
    impact: Literal["high", "medium", "low"] = Field(description="Expected impact level")
    target_proposition: str = Field(description="Symbol of the proposition this recommendation supports")
    expected_conclusion_improvement: ExpectedConclusionImprovement = Field(description="Expected improvement in conclusion scores")
    propositions: list[ImprovementProposition] = Field(description="Array of propositions in this recommendation set")


class ImprovementSuggestions(BaseModel):
    """Complete improvement suggestions from the improvement agent"""
    recommendations: list[ImprovementRecommendation] = Field(description="Array of improvement recommendations")

