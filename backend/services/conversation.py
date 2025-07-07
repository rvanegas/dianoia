from openai import OpenAI
from config import OPENAI_API_KEY
from core.utils import logger
import json

from core.utils import logger
from .system_prompt import (welcome_system_prompt, development_system_prompt,
    justify_system_prompt, re_evaluate_system_prompt)
from models.argument import (ArgumentPrompt, ArgumentResponse, ThesesPrompt,
    JustifyPrompt, Step, proofread_response)

client = OpenAI(api_key=OPENAI_API_KEY)

theses_response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "response",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "thesis": {"type": "string"},
                "counter_thesis": {"type": "string"},
                "presupposition": {"type": "string"}
            },
            "required": ["thesis", "counter_thesis", "presupposition"],
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
            "truth": {"type": "number"},
            "valid": {"type": "number"}
        },
        "required": ["index", "proposition", "justifiers", "truth", "valid"],
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
                "assumptions": argument_format,
                "argument": argument_format,
                "counter_argument": argument_format
            },
            "required": ["argument", "counter_argument", "assumptions"],
            "additionalProperties": False
        }
    }
}

justify_response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "response",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "propositions": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["propositions"],
            "additionalProperties": False
        }
    }
}

re_evaluate_response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "response",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "truth": {
                    "type": "array",
                    "items": {"type": "number"}
                },
                "valid": {"type": "number"}
            },
            "required": ["truth", "valid"],
            "additionalProperties": False
        }
    }
}

def develop_theses(theses_prompt):
    messages = [{
        "role": "system",
        "content": welcome_system_prompt
    },
    {
        "role": "user",
        "content": theses_prompt.json()
    }]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        response_format=theses_response_format,
    )
    theses = response.choices[0].message.content
    return theses

def develop_argument(argument_prompt):
    messages = [{
        "role": "system",
        "content": development_system_prompt
    },
    {
        "role": "user",
        "content": argument_prompt.json()
    }]

    # logger.debug(f"messages {len(messages)}")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        response_format=argument_response_format,
    )
    content = response.choices[0].message.content

    # logger.debug("argument_prompt")
    # logger.debug(argument_prompt.argument)
    # logger.debug("argument_response")
    # logger.debug(argument_response.argument)

    args = json.loads(content)
    argument_response = ArgumentResponse.parse_obj(args)
    errors = proofread_response(argument_prompt, argument_response)

    # logger.debug(f"argument_prompt: {argument_prompt}")
    # logger.debug(f"argument_response: {argument_response}")
    # logger.debug(f"errors['argument']: {errors['argument']}")
    # logger.debug(f"errors['counter_argument']: {errors['counter_argument']}")

    return content, errors

def justify_proposition(prompt: JustifyPrompt):

    logger.debug('prompt', prompt)
    prompt.validate_step_id()

    messages = [{
        "role": "system",
        "content": justify_system_prompt
    },
    {
        "role": "user",
        "content": prompt.json()
    }]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        response_format=justify_response_format,
    )
    content = response.choices[0].message.content
    jcontent = json.loads(content)
    logger.debug(f"({jcontent})")

    new_propositions = json.loads(content)["propositions"]
    for p in new_propositions:
        new_arg = prompt.insert_proposition(p)

    evaluations = re_evaluate(new_arg)

    logger.debug(f"evaluations{evaluations}")

    new_args = prompt.json()
    logger.debug(f"new_arg{new_arg}")
    logger.debug(f"new_args{new_args}")

    return new_args, None

def re_evaluate(steps: list[Step]):
    props = [s.proposition for s in steps]

    messages = [{
        "role": "system",
        "content": re_evaluate_system_prompt
    },
    {
        "role": "user",
        "content": json.dumps(props)
    }]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        response_format=re_evaluate_response_format,
    )
    content = response.choices[0].message.content

    evaluations = json.loads(content)
    logger.debug(f"evaluations{evaluations}")

    return evaluations
