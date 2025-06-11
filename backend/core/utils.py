import logging

logger = logging.getLogger("dianoia")
logger.setLevel(logging.DEBUG)  # or INFO, WARNING, etc.
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
