"""
The response of GET /api/agents/results, as published in /openapi.json.

This is dianoia's contract with its clients: Roxana generates its TypeScript
types from it and mdc parses what it describes. Each agent's result_content is
typed by its agent_type, a discriminated union, so a client can narrow on it.

Declared on the route as its documented response rather than enforced as its
response_model: a mismatch must never turn a working response into a 500 for
a client. Drift is caught in tests instead — src/tests/test_api_contract.py
validates a recorded real response against these models, and the models
written here forbid fields they do not declare, so an agent that starts
returning something new fails that test until it is declared. Re-record the
fixture whenever an agent's output changes.
"""

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

from schemas.step import ImprovementRecommendation, Step


class _Strict(BaseModel):
    # Fields with defaults are still always serialized, so they are published
    # as required; Definition is the one exception.
    model_config = ConfigDict(extra="forbid", json_schema_serialization_defaults_required=True)


# -- result_content, one per agent ---------------------------------------------

class TruthEvaluation(_Strict):
    symbol: str
    truth_value: float
    reasoning: str


class IncoherentSet(_Strict):
    symbols: list[str]
    incoherence_value: float


class TruthEvaluatorResult(_Strict):
    truth_evaluations: list[TruthEvaluation]
    incoherent_sets: list[IncoherentSet]
    argument: list[Step]


class ValidityEvaluation(_Strict):
    symbol: str
    validity_value: float
    reasoning: str


class ContentValidityEvaluatorResult(_Strict):
    validity_evaluations: list[ValidityEvaluation]
    logical_issues: list[str]
    argument: list[Step]


class PhrasingEvaluation(_Strict):
    symbol: str
    issues: list[str]
    recommendation: str


class PhrasingEvaluatorResult(_Strict):
    phrasing_evaluations: list[PhrasingEvaluation]
    argument: list[Step]


class FormalizationItem(_Strict):
    symbol: str
    ascii: str
    json_structure: str


class Definition(_Strict):
    # arity really is absent on constants, so it stays optional in the schema.
    model_config = ConfigDict(extra="forbid", json_schema_serialization_defaults_required=False)

    symbol: str
    value: str
    arity: int | None = Field(default=None, description="Predicates only; absent on constants")


class Definitions(_Strict):
    predicates: list[Definition]
    constants: list[Definition]


class FormalizerResult(_Strict):
    formalizations: list[FormalizationItem]
    definitions: Definitions
    confidence: float
    reasoning: str
    formalization_mode: str
    argument: list[Step]


class PropositionEvaluation(_Strict):
    symbol: str
    validity: float
    reasoning: str


class FormEvaluatorResult(_Strict):
    proposition_evaluations: list[PropositionEvaluation]
    argument_validity: float
    logical_issues: list[str]
    evaluation_mode: str
    argument: list[Step]


class EvaluationContext(_Strict):
    content_evaluations_count: int
    formal_evaluations_count: int
    conclusion_proposition: str
    total_evaluations: int


class ImproverResult(_Strict):
    recommendations: list[ImprovementRecommendation]
    improvement_mode: str
    argument: list[Step]
    evaluation_context: EvaluationContext


class NameGeneratorResult(_Strict):
    name: str


# -- one stored result, typed by its agent ---------------------------------------

class TargetMetadata(_Strict):
    target_type: str
    target_content: str


class _AgentResultBase(_Strict):
    operation: str
    confidence: float
    reasoning: str
    target_metadata: TargetMetadata
    snapshot_id: str
    processed_at: float = Field(description="Unix time, seconds")


class TruthEvaluatorAgentResult(_AgentResultBase):
    agent_type: Literal["truth_evaluator"]
    result_content: TruthEvaluatorResult


class ContentValidityEvaluatorAgentResult(_AgentResultBase):
    agent_type: Literal["content_validity_evaluator"]
    result_content: ContentValidityEvaluatorResult


class PhrasingEvaluatorAgentResult(_AgentResultBase):
    agent_type: Literal["phrasing_evaluator"]
    result_content: PhrasingEvaluatorResult


class FormalizerAgentResult(_AgentResultBase):
    agent_type: Literal["formalizer"]
    result_content: FormalizerResult


class FormEvaluatorAgentResult(_AgentResultBase):
    agent_type: Literal["form_evaluator"]
    result_content: FormEvaluatorResult


class ImproverAgentResult(_AgentResultBase):
    agent_type: Literal["improver"]
    result_content: ImproverResult


class NameGeneratorAgentResult(_AgentResultBase):
    agent_type: Literal["name_generator"]
    result_content: NameGeneratorResult


AgentResult = Annotated[
    Union[
        TruthEvaluatorAgentResult,
        ContentValidityEvaluatorAgentResult,
        PhrasingEvaluatorAgentResult,
        FormalizerAgentResult,
        FormEvaluatorAgentResult,
        ImproverAgentResult,
        NameGeneratorAgentResult,
    ],
    Field(discriminator="agent_type"),
]


# -- the response -------------------------------------------------------------------

class ActiveTask(_Strict):
    task_id: str
    agent_type: str
    status: str
    conversation_id: str
    snapshot_id: str


class AgentResultsResponse(_Strict):
    conversation_id: str
    snapshot_id: str
    results_by_agent: dict[str, list[AgentResult]] = Field(
        description="Keyed by agent_type; each list holds that agent's results, newest last"
    )
    total_count: int
    agent_types: list[str]
    tasks_complete: bool = Field(description="True once every task for this conversation/snapshot has finished")
    active_tasks: list[ActiveTask]
    active_task_count: int
    conversation_name: str | None


class EvaluateStarted(_Strict):
    """What POST /api/argument/evaluate returns: the ids to poll /api/agents/results with."""
    conversation_id: str
    snapshot_id: str
