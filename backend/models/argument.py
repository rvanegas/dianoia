from pydantic import BaseModel
from core.utils import logger

thesis_response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "response",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "thesis": {"type": "string"},
                "counter_thesis": {"type": "string"},
                "explanation": {"type": "string"}
            },
            "required": ["thesis", "counter_thesis", "explanation"],
            "additionalProperties": False
        }
    }
}

argument_format = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "index": {"type": "string"},
            "proposition": {"type": "string"},
            "justifiers": {
                "type": "array",
                "items": {"type": "string"}
            },
        },
        "required": ["index", "proposition", "justifiers"],
        "additionalProperties": False
    }
}

argument_response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "response",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "argument": argument_format,
                "counter_argument": argument_format,
                "explanation": {"type": "string"}
            },
            "required": ["argument", "counter_argument", "explanation"],
            "additionalProperties": False
        }
    }
}

class ThesisResponse(BaseModel):
    thesis: str
    counter_thesis: str
    explanation: str

class Step(BaseModel):
    index: str
    proposition: str
    justifiers: list[str]

class ArgumentResponse(BaseModel):
    argument: list[Step]
    counter_argument: list[Step]
    explanation: str

def proofreadResponse(messages, prompt, content):
    def verify_uniqueness(steps):
        seen = set()
        duplicates = []
        for step in steps:
            if step.proposition in seen:
                duplicates.append(step.index)
            else:
                seen.add(step.proposition)
        return duplicates

    def verify_index_stability(prev_steps, curr_steps):
        prev_map = {step.proposition: step.index for step in prev_steps}
        mismatches = []
        for step in curr_steps:
            if step.proposition in prev_map and step.index != prev_map[step.proposition]:
                mismatches.append((prev_map[step.proposition], step.index))
        return mismatches

    def verify_dependency_order(steps):
        index_order = {step.index: i for i, step in enumerate(steps)}
        violations = []
        for i, step in enumerate(steps):
            for justifier in step.justifiers:
                if justifier not in index_order:
                    violations.append((step.index, justifier, "missing justifier"))
                elif index_order[justifier] >= i:
                    violations.append((step.index, justifier, "future dependency"))
        return violations

    def verify_final_conclusion(steps):
        if not steps:
            return None
        return None if steps[-1].justifiers else "Final proposition must be conclusion, not premise"

    def verify_conclusion_dependency(steps):
        # Basic check: trace dependencies backward from the final conclusion
        if not steps:
            return None

        index_map = {step.index: step for step in steps}
        reachable = set()
        to_visit = list(steps[-1].justifiers)

        while to_visit:
            current = to_visit.pop()
            if current in reachable:
                continue
            reachable.add(current)
            to_visit.extend(index_map.get(current, Step(index=current, proposition="", justifiers=[])).justifiers)

        unused = [step.index for step in steps[:-1] if step.index not in reachable]
        return unused

    theses = ThesisResponse.parse_raw(prompt.history[1]['content'])
    response = ArgumentResponse.parse_raw(content)
    prevResponses = [m for m in messages if m["role"] == "assistant"]
    prevResponse = prevResponses[-1] if prevResponses else None

    errors = {
        "argument": [],
        "counter_argument": []
    }

    for label in ["argument", "counter_argument"]:
        prev_steps = getattr(prevResponse, label, [])
        curr_steps = getattr(response, label, [])

        # Uniqueness
        duplicates = verify_uniqueness(curr_steps)
        if duplicates:
            errors[label].append(f"Duplicate propositions found at indices: {duplicates}")

        # Index stability
        mismatches = verify_index_stability(prev_steps, curr_steps)
        if mismatches:
            errors[label].append(f"Index changes detected: {mismatches}")

        # Contribution to conclusion
        unused = verify_conclusion_dependency(curr_steps)
        if unused:
            errors[label].append(f"Propositions not contributing to conclusion: {unused}")

        # Order conformance
        order_violations = verify_dependency_order(curr_steps)
        if order_violations:
            formatted = [(s, j, reason) for s, j, reason in order_violations]
            errors[label].append(f"Dependency order violations: {formatted}")

        # Conclusion position
        conclusion_error = verify_final_conclusion(curr_steps)
        if conclusion_error:
            errors[label].append(conclusion_error)

    # Agreement of conclusions with theses
    if len(response.argument) and theses.thesis != response.argument[-1].proposition:
        errors['argument'].append("Argument conclusion does not match thesis.")

    if len(response.counter_argument) > 0 and theses.counter_thesis != response.counter_argument[-1].proposition:
        errors['argument'].append("Counter-argument conclusion does not match counter-thesis.")

    return errors
