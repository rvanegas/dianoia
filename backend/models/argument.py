from pydantic import BaseModel

argument_format = {
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "index": {"type": "string"},
      "proposition": {"type": "string"},
      "justifier": {"type": "string"},
      "changed": {"type": "boolean"}
    },
    "required": ["index", "proposition", "justifier", "changed"],
    "additionalProperties": False
  }
}

response_format = {
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

class Step(BaseModel):
    index: str
    proposition: str
    justifier: str
    changed: bool

class ArgumentResponse(BaseModel):
    argument: list[Step]
    counter_argument: list[Step]
    explanation: str

def proofreadResponse(prevResponse, response):
    pass
