import json
import time
from functools import wraps

import src.log_util as log_util


def wrapper(method):
    """This method wraps every function within a class that inherits from Base.

    Incredible wrapping SO answer https://stackoverflow.com/a/1594484 (for future ref)

    If the keyword argument exec_tm=True is passed to any of these methods, the function is prepended
      and post-pended with logging for the execution time of the function
    Otherwise the method just runs as normal

    The 'wrapped' method is the method that actually replaces all the normal method calls, with the
      normal method call inside

    :param function method: method to wrap
    :return function: wrapped method with execution time functionality
    """
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        # get the passed value of exec_tm if it exists, otherwise set default to False
        exec_tm = kwargs.pop("exec_tm") if kwargs.get("exec_tm") else False

        # the entire wrapping only happens if exec_tm is True
        if exec_tm:
            # record a start time for the function
            start_time = time.time()

            # Try to log calling the function
            try:
                self.logger.info(f"Calling function {method.__name__}")
            except AttributeError:
                pass

            # call the original method with the passed arguments and keyword arguments, and store the result
            output = method(self, *args, **kwargs)

            # Try to log how long the function took
            try:
                self.logger.duration(method.__name__, start_time=start_time)
            except AttributeError:
                pass

            # return the output of the original function
            return output
        else:
            # just run the method as normal
            return method(self, *args, **kwargs)
    return wrapped


class BaseMeta(type):
    """This acts as a metaclass for the Base class.

    All this class does is override the magic __new__ constructor, iterate through the class properties,
      and if a property is a callable (function), wrap it with the execution time logic. It then returns
      the modified class, and when any class is called with this metaclass, this __new__ is called.
      Inheritance looks like type -> BaseMeta -> Base -> other classes

    See explanation: https://stackoverflow.com/a/6581949
    """
    def __new__(mcs, classname, bases, class_dict):
        new_class_dict = {}
        for attributeName, attribute in class_dict.items():
            if callable(attribute):
                # if the attribute is a callable, wrap it with the execution time logic
                attribute = wrapper(attribute)
            new_class_dict[attributeName] = attribute
        return super(BaseMeta, mcs).__new__(mcs, classname, bases, new_class_dict)


class Base(metaclass=BaseMeta):
    def __init__(self, settings=False, log_path=None):
        """Acts as a base class for most classes. Provides automatic logging, settings creation,
          common methods and execution time analysis

        :param bool settings: If true, load settings from the config file
        :param str log_path: Path to store the log. If not set, get the global log
        """

        # record a class-wide start time
        self.start_time = time.time()

        # Load the settings file
        if settings:
            with open("settings.json", "r") as read_file:
                self.settings = json.load(read_file)["settings"]

        # The global logger is named log, which means there is only ever one instance
        # if passed a path to output the log to, create the logger at that path
        # otherwise retrieve the standard logger
        if log_path:
            self.logger = log_util.create_logger('log', log_path)
        else:
            # if a logger already exists for script
            self.logger = log_util.get_logger('log')

    def close(self, start_time=None):
        """Outputs the duration of the programme """
        start_time = start_time if start_time else self.start_time
        self.logger.finished(f"Script", start_time=start_time)
