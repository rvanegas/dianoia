"""Extract a structured argument from plain text using Claude."""

from services.conversation import Gpt

_EXTRACTION_SYSTEM_PROMPT = """
You are an expert in logical argumentation. Given a piece of text, identify the argument
it contains and structure it as a set of propositions with logical dependencies.

### Output format

Return a JSON object with two lists:

- **assumptions**: Background premises the author takes as given — propositions the
  argument rests on but does not itself argue for. These have no justifiers.

- **argument**: The chain of reasoning from those premises toward the conclusion.
  Each step must list the symbols of the steps that directly justify it in `justifiers`.
  The final step (the conclusion) is the proposition that all others ultimately support.

Each proposition is a Step object:
  - symbol: A single uppercase letter A–Z, assigned in order across both lists
  - proposition: A single clear declarative sentence
  - justifiers: List of symbols that directly support this step (empty for assumptions
    and the first independent argument steps)
  - truth_score: Always ""

### Guidelines

- Keep propositions atomic — one claim per step
- The last step in `argument` should be the main conclusion
- Assumptions are foundational premises that require no further justification in this text
- Intermediate argument steps each derive from one or more prior steps or assumptions
- Do not fabricate claims not present in the text
- Aim for 2–5 assumptions and 3–6 argument steps for typical texts; more is acceptable
  for complex arguments
- Symbols are assigned in order: A, B, C, … across assumptions first, then argument steps

### Example

Input text: "Regular exercise strengthens the cardiovascular system. A strong
cardiovascular system leads to longer life expectancy. Exercise also reduces stress
and improves mental health. Therefore, people who exercise regularly tend to live
healthier and longer lives."

Output:
{
  "assumptions": [
    {"symbol": "A", "proposition": "Regular exercise strengthens the cardiovascular system.", "justifiers": [], "truth_score": ""},
    {"symbol": "B", "proposition": "Exercise reduces stress and improves mental health.", "justifiers": [], "truth_score": ""}
  ],
  "argument": [
    {"symbol": "C", "proposition": "A strong cardiovascular system leads to longer life expectancy.", "justifiers": ["A"], "truth_score": ""},
    {"symbol": "D", "proposition": "People who exercise regularly tend to live healthier and longer lives.", "justifiers": ["A", "B", "C"], "truth_score": ""}
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

_gpt_extract = Gpt(
    instructions=_EXTRACTION_SYSTEM_PROMPT,
    response_format_base={
        "type": "object",
        "properties": {
            "assumptions": {"type": "array", "items": _STEP_SCHEMA},
            "argument":    {"type": "array", "items": _STEP_SCHEMA},
        },
        "required": ["assumptions", "argument"],
        "additionalProperties": False,
    },
)


def extract_argument(text: str) -> dict:
    """Extract a structured argument from plain text.

    Returns an Arguments-compatible dict with 'assumptions' and 'argument' keys.
    Raises ValueError if extraction fails or produces an empty argument.
    """
    import json

    raw = _gpt_extract.call(text, file_ids=None)
    result = json.loads(raw)

    if not result.get("argument"):
        raise ValueError("extraction produced no argument steps")

    return result
