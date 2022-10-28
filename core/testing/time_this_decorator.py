from typing import Callable
from time import perf_counter_ns


_calls: dict[Callable, list[int]] = {}
def _add_elapsed(func: Callable, elapsed: int, max_values: int) -> None:
    assert max_values > 0
    if func not in _calls:
        _calls[func] = []

    values = _calls[func]
    values.append(elapsed)
    while len(values) > max_values:
        values.pop(0)

def _get_elapsed_average(func, values_to_use_amount: int) -> int | None:
    assert values_to_use_amount > 0
    if func not in _calls:
        return None

    values = _calls[func]
    if len(values) < values_to_use_amount:
        return None

    to_use: list[int] = values[-values_to_use_amount:] # take values_to_use_amount count of values from end
    return sum(to_use) // len(to_use)


def time_this(average_count: int = 0):
    """A decorator that prints the execution time of the decorated function."""

    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            start = perf_counter_ns()
            output = func(*args, **kwargs)
            stop = perf_counter_ns()

            elapsed = stop - start

            msg = f"Execution of function \"{func.__name__}\" took {elapsed} nanoseconds."
            if average_count > 0:
                _add_elapsed(func, elapsed, average_count)
                average = _get_elapsed_average(func, average_count)
                average_txt: str = f"{average} ns" if average is not None else "N/A"
                msg += f" (Average: {average_txt})"

            print(msg)
            return output

        return wrapper

    return decorator
