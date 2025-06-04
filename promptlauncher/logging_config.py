import logging

LOG_FORMAT = "[%(asctime)s] %(levelname)s:%(name)s: %(message)s"

def setup_logging(level=logging.INFO):
    """Configure application-wide logging.

    If the root logger is already configured, this function does nothing.
    Returns the root logger instance.
    """
    root = logging.getLogger()
    if root.handlers:
        return root
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root.setLevel(level)
    root.addHandler(handler)

    # Reduce verbosity for third-party libraries
    logging.getLogger("paramiko").setLevel(logging.WARNING)
    return root
