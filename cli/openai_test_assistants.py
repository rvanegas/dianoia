import time
import openai
from core.utils import logger
from services.openaiclient import client

assistant_id="asst_IuHKc1qUi3gm59Sm37xJOeQ1"
vector_store_id="vs_6875f8b4aa4c81918b0db7c0b0c68fc3"
run_id="run_jbeyQLENMhTlI5e0IFyZi6Mr"
thread_id="thread_H7V5NcyVpn5PqXxOQQlpkc1y"

def create():
    response = client.beta.assistants.update("asst_IuHKc1qUi3gm59Sm37xJOeQ1", 
        instructions="""
            You must answer only using the retrieved documents. 
            If no documents are retrieved, respond: 'No context retrieved.' 
            Do not guess. Put the answer in the 'thesis' property.'
        """,
        tool_resources={
            "file_search": {
                "vector_store_ids": [vector_store_id]
            }
        })

    # thread = client.beta.threads.create()
    # client.beta.threads.messages.create(
    #     thread_id=thread.id,
    #     role="user",
    #     content="Tell me about the article."
    # )
    # run = client.beta.threads.runs.create(
    #     thread_id=thread.id,
    #     assistant_id=assistant_id
    # )

    # run = client.beta.threads.create_and_run(
    #     thread={
    #         "messages": [{
    #             "role": "user",
    #             "content": "Tell me about the article.",
    #         }],
    #     },
    #     assistant_id=assistant_id
    # )


    run = client.beta.threads.create_and_run_poll(
        thread={
            # "tool_resources": {
            #     "file_search": {
            #         "vector_store_ids": [vector_store_id]
            #     }
            # }
            "messages": [{
                "role": "user",
                "content": "Tell me about the article.",
            }],
        },
        assistant_id=assistant_id
    )

    logger.debug(f"r {run} ")
    logger.debug(f"r {run.status} ")

def retrieve_run():
    run = client.beta.threads.runs.retrieve(run_id, thread_id=thread_id)
    logger.debug(f"r {run}")
    logger.debug(f"r {run.status} ")

def list_msgs():
    msgs = client.beta.threads.messages.list(thread_id)
    logger.debug(f"m {msgs}")

# help(openai.types.beta.thread_create_and_run_params.ThreadCreateAndRunParamsBase)

# create()
# retrieve_run()
# list_msgs()
