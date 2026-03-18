import logging
from contextvars import ContextVar
import os


class CorrelationIDFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = correlation_id_context.get()
        return True  # This is required to let the log pass else it gets filtered out


correlation_id_context = ContextVar("correlation_id", default="NA")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.getLogger().setLevel(LOG_LEVEL)
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(module)s | %(funcName)s | "
                              "[ID: %(correlation_id)s] | %(message)s")
cor_id_filter = CorrelationIDFilter()

handlers = [
    logging.StreamHandler(),
    logging.FileHandler("app.log", "w")
]

for handler in handlers:
    handler.setFormatter(formatter)
    handler.setLevel(LOG_LEVEL)
    handler.addFilter(cor_id_filter)
    logging.getLogger().addHandler(handler)
