# -*- coding: utf-8 -*-
import inspect
from functools import wraps
from logging import getLogger


def handle_exception_by_log(func):
    """Handles all the `func` exceptions by an error log"""
    func_module_name = inspect.getmodule(func).__name__

    @wraps(func)
    def inner(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception:
            getLogger(func_module_name).exception(
                f"An error occured during the {func_module_name}.{func.__name__} execution:"
            )

    return inner
