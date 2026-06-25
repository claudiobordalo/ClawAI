import logging

class ColoredFormatter(logging.Formatter):
    """
    A custom logging formatter that adds color to log messages.
    """

    def __init__(self, fmt=None, datefmt=None, style='%'):
        raise NotImplementedError("Subclasses must implement this method.")

    def format(self, record: logging.LogRecord) -> str:
        raise NotImplementedError("Subclasses must implement this method.")