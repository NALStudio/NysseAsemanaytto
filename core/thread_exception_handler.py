from threading import ExceptHookArgs
from core import logging


def thread_excepthook(args: ExceptHookArgs):
    logging.dump_exception_with_params(args.exc_type, args.exc_value, args.exc_traceback, args.thread, "excepthook")
