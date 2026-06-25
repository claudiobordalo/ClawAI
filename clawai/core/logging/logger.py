import logging

class BaseLogger:
    def __new__(cls):
        raise NotImplementedError("Subclasses must implement this method.")

    def __init__(self):
        raise NotImplementedError("Subclasses must implement this method.")

    @staticmethod
    def configure():
        raise NotImplementedError("Subclasses must implement this method.")

    @staticmethod
    def get_logger(name):
        raise NotImplementedError("Subclasses must implement this method.")