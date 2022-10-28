from typing import Callable
from time import perf_counter_ns


def time_this(func: Callable):
    """A decorator that prints the execution time of the decorated function."""

    def wrapper(*args, **kwargs):
        start = perf_counter_ns()
        output = func(*args, **kwargs)
        stop = perf_counter_ns()

        print(f"Execution of function \"{func.__name__}\" took {stop - start} nanoseconds.")
        return output

    return wrapper
