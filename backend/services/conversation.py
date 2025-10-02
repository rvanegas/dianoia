from openai import OpenAI
from config import OPENAI_API_KEY
from core.utils import logger
import json

from core.utils import logger
from .system_prompt import system_welcome_prompt, system_development_prompt
from models.argument import ArgumentPrompt, ThesesPrompt, argument_response_format, theses_response_format, proofread_response

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
    content = response.choices[0].message.content
    return content

def develop_argument(argument_prompt):
    # trials = 1
    messages = [{
        "role": "system",
        "content": system_development_prompt
    },
    {
        "role": "user",
        "content": argument_prompt.json()
    }]
    while True:
        # trials += 1
        logger.debug(f"messages {len(messages)}")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            response_format=argument_response_format,
        )
        content = response.choices[0].message.content
        break

        if welcome:
            break
        else:
            errors = proofread_response(messages, prompt, content)
            if len(errors['argument']) == 0 and len(errors['counter_argument']) == 0:
                break            
            logger.debug(f"content: {content}")
            logger.debug(f"errors: {errors}")
            if trials > 3:
                break
            messages += [{
                "role": "assistant",
                "content": content
            },
            {
                "role": "system",
                "content": "The generated argument fails some checks. " +
                    "The following are errors. Try again. In the " + 
                    "explanation, do not mention that it is a retrial " +
                    "since user won't see the failed response."
            },
            {
                "role": "system",
                "content": json.dumps(errors)
            }]

    return content
