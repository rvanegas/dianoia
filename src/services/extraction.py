"""Extract a structured argument from plain text using Claude."""

from services.conversation import ModelAgent

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

### Guidelines

- Keep propositions atomic — one claim per step
- The last step in `argument` should be the main conclusion
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
    {"symbol": "2", "proposition": "Exercise reduces stress and improves mental health.", "justifiers": [], "truth_score": ""},
    {"symbol": "3", "proposition": "A strong cardiovascular system leads to longer life expectancy.", "justifiers": ["1"], "truth_score": ""},
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

_gpt_extract = ModelAgent(
    instructions=_EXTRACTION_SYSTEM_PROMPT,
    response_format_base=_RESPONSE_FORMAT,
)


def extract_argument(text: str, max_props: int | None = None) -> dict:
    """Extract a structured argument from plain text.

    Returns an Arguments-compatible dict with an 'argument' key.
    Raises ValueError if extraction fails or produces an empty argument.
    """
    import json

    if max_props is not None:
        extra = (
            f"\n- Use at most {max_props} propositions in total; merge or drop minor"
            " claims to stay within this limit"
        )
        agent = ModelAgent(
            instructions=_EXTRACTION_SYSTEM_PROMPT + extra,
            response_format_base=_RESPONSE_FORMAT,
        )
    else:
        agent = _gpt_extract

    raw = agent.call(text, file_ids=None)
    result = json.loads(raw)

    if not result.get("argument"):
        raise ValueError("extraction produced no argument steps")

    return result
