from pydantic import BaseModel

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

class ThesisResponse(BaseModel):
    thesis: str
    counter_thesis: str
    explanation: str
