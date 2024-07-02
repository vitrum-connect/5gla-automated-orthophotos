import inspect
import logging
import os.path
from datetime import datetime


class CustomLogger:
    """ A custom Logger class

    Ensures that every log entry has the same schema
    """

    def __init__(self):
        file_dir = os.path.dirname(__file__)
        # Go up one directory to the project root
        file_dir = os.path.dirname(file_dir)
        log_dir = file_dir + "/logs"
        self.logger = logging.getLogger('local_app')
        self.logger.setLevel(logging.DEBUG)
        current_date = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(log_dir, f'{current_date}.log')
        self.file_handler = logging.FileHandler(log_file)
        log_format = '[%(asctime)s] %(levelname)s [%(module)s.%(funcName)s:%(lineno)d]: %(message)s'
        formatter = logging.Formatter(log_format)
        self.file_handler.setFormatter(formatter)

    def log_info(self, message):
        """ Logs a info message

        :param message: The log message
        :return:
        """

        self.add_file_handler()

        caller_frame = inspect.stack()[1]
        caller_module = inspect.getmodule(caller_frame[0]).__name__
        caller_function = caller_frame.function
        self.logger.info(f'[{caller_module}.{caller_function}]: {message}')

        self.remove_file_handler()

    def log_warning(self, message):
        """ Logs a warning message

        :param message: The log message
        :return:
        """

        self.add_file_handler()

        caller_frame = inspect.stack()[1]
        caller_module = inspect.getmodule(caller_frame[0]).__name__
        caller_function = caller_frame.function
        self.logger.warning(f'[{caller_module}.{caller_function}]: {message}')

        self.remove_file_handler()

    def add_file_handler(self):
        """ Adds the file handler to ensure that log files can be written and modified

        :return:
        """
        self.logger.addHandler(self.file_handler)

    def remove_file_handler(self):
        """ Removes and closes the file handler to ensure the file can be used by another process

        :return:
        """
        self.logger.removeHandler(self.file_handler)
        self.file_handler.close()
