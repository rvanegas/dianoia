"""Extract a structured argument from plain text using Claude."""

from services.conversation import ModelAgent
from services.structural_conditions import STRUCTURAL_CONDITIONS

_EXTRACTION_SYSTEM_PROMPT = """
You are an expert in logical argumentation. Given a piece of text, identify the argument
it contains and structure it as a set of propositions with logical dependencies.

### Output format

Return a JSON object with a single list:

- **argument**: Every proposition in the chain of reasoning toward the conclusion,
  in one flat list. Each step must list the symbols of the steps that directly justify
  it in `justifiers`. A step with no justifiers is simply a premise being introduced
  without derivation from an earlier step in this text — it is not a special category;
  it is an ordinary proposition subject to the same downstream truth and validity
  evaluation as every other step. Do not label, flag, or otherwise distinguish
  premises from derived steps beyond their (possibly empty) `justifiers` list. The
  final step (the conclusion) is the proposition that all others ultimately support.

Each proposition is a Step object:
  - symbol: A positive integer starting at 1, assigned in order
  - proposition: A single clear declarative sentence
  - justifiers: List of symbols that directly support this step (empty if the step is
    a premise not derived from any other step in this text)
  - truth_score: Always ""

### Structural requirements

Every extracted argument must satisfy all three of these conditions:

""" + STRUCTURAL_CONDITIONS + """

Before returning, check every step against these three requirements and revise
any violation.

### Guidelines

- Keep propositions atomic — one claim per step
- Every step — premise or derived — is treated identically by the rest of the system:
  it will be evaluated for truth and (if it has justifiers) content validity. Nothing
  in this text is "given" or exempt from evaluation; do not reason as if some
  propositions are assumed true
- Intermediate argument steps each derive from one or more prior steps
- Do not fabricate claims not present in the text
- Aim for 5–10 propositions total for typical texts; more is acceptable for complex
  arguments
- Symbols are assigned in order: 1, 2, 3, …

### Example

Input text: "Regular exercise strengthens the cardiovascular system. A strong
cardiovascular system leads to longer life expectancy. Exercise also reduces stress
and improves mental health. Therefore, people who exercise regularly tend to live
healthier and longer lives."

Output:
{
  "argument": [
    {"symbol": "1", "proposition": "Regular exercise strengthens the cardiovascular system.", "justifiers": [], "truth_score": ""},
    {"symbol": "2", "proposition": "A strong cardiovascular system leads to longer life expectancy.", "justifiers": [], "truth_score": ""},
    {"symbol": "3", "proposition": "Exercise reduces stress and improves mental health.", "justifiers": [], "truth_score": ""},
    {"symbol": "4", "proposition": "People who exercise regularly tend to live healthier and longer lives.", "justifiers": ["1", "2", "3"], "truth_score": ""}
  ]
}
"""

_STEP_SCHEMA = {
    "type": "object",
    "properties": {
        "symbol":      {"type": "string"},
        "proposition": {"type": "string"},
        "justifiers":  {"type": "array", "items": {"type": "string"}},
        "truth_score": {"type": "string"},
    },
    "required": ["symbol", "proposition", "justifiers", "truth_score"],
    "additionalProperties": False,
}

_RESPONSE_FORMAT = {
    "type": "object",
    "properties": {
        "argument":    {"type": "array", "items": _STEP_SCHEMA},
    },
    "required": ["argument"],
    "additionalProperties": False,
}

_STANCES = """

### Participants and their stances

The text is a conversation among these participants: {names}. Extract the one
argument they all took part in: a proposition one participant rejects is still
part of it, in the form the participant who asserted it gave it. Where they
disagree, keep the competing propositions as separate steps rather than choosing
between them.

Each step also lists, by the names above exactly as given:
  - accepted: the participants who assert or agree with it in the text
  - rejected: the participants who deny or dispute it in the text

A participant who takes no stance on a step is in neither list. Never infer a
stance the text does not show.
"""


def _response_format(participants: list[str]) -> dict:
    """The response schema, its steps carrying stances when there are participants."""
    if not participants:
        return _RESPONSE_FORMAT
    names = {"type": "array", "items": {"type": "string", "enum": participants}}
    step = {
        **_STEP_SCHEMA,
        "properties": {**_STEP_SCHEMA["properties"], "accepted": names, "rejected": names},
        "required": [*_STEP_SCHEMA["required"], "accepted", "rejected"],
    }
    return {**_RESPONSE_FORMAT, "properties": {"argument": {"type": "array", "items": step}}}


_gpt_extract = ModelAgent(
    instructions=_EXTRACTION_SYSTEM_PROMPT,
    response_format_base=_RESPONSE_FORMAT,
    max_tokens=8192,
)


def extract_argument(text: str, max_props: int | None = None, participants: list[str] | None = None) -> dict:
    """Extract a structured argument from plain text.

    With participants, the names a conversation's people go by, each step
    also lists those who accept it and those who reject it.

    Returns an Arguments-compatible dict with an 'argument' key.
    Raises ValueError if extraction fails or produces an empty argument.
    """
    import json

    participants = list(dict.fromkeys(p for p in participants or [] if p.strip()))
    instructions = _EXTRACTION_SYSTEM_PROMPT
    if max_props is not None:
        instructions += (
            f"\n- Use at most {max_props} propositions in total; merge or drop minor"
            " claims to stay within this limit"
        )
    if participants:
        instructions += _STANCES.format(names=", ".join(participants))
    if instructions == _EXTRACTION_SYSTEM_PROMPT:
        agent = _gpt_extract
    else:
        agent = ModelAgent(
            instructions=instructions,
            response_format_base=_response_format(participants),
            max_tokens=8192,
        )

    raw = agent.call(text, file_ids=None)
    result = json.loads(raw)

    if not result.get("argument"):
        raise ValueError("extraction produced no argument steps")

    # Only the names given, each once, never in both lists.
    for step in result["argument"] if participants else ():
        accepted = [n for n in dict.fromkeys(step.get("accepted") or []) if n in participants]
        step["accepted"] = accepted
        step["rejected"] = [n for n in dict.fromkeys(step.get("rejected") or []) if n in participants and n not in accepted]

    return result
