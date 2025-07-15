"""simple tools to import anywhere"""
import logging
from datetime import datetime

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

def prettytimestamp(timestamp):
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")
