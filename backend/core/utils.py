"""simple tools to import anywhere"""
import logging

logger = logging.getLogger("dianoia")
logger.setLevel(logging.DEBUG)  # or INFO, WARNING, etc.
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

def find_index(array, predicate):
    """like findIndex() in JS"""
    for index, item in enumerate(array):
        if predicate(item):
            return index
    return -1
