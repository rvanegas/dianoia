from openai import OpenAI
from config import OPENAI_API_KEY
from core.utils import logger
import json

from core.utils import logger
from .system_prompt import system_welcome_prompt, system_development_prompt
from models.argument import ( ArgumentPrompt, ArgumentResponse, ThesesPrompt,
    argument_response_format, theses_response_format, proofread_response )

client = OpenAI(api_key=OPENAI_API_KEY)

def develop_theses(theses_prompt):
    messages = [{
        "role": "system",
        "content": system_welcome_prompt
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
        "content": system_development_prompt
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
