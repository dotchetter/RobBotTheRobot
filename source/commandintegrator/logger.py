import os
import json
import logging
import functools
from pathlib import Path

"""
Module details:
    This module contains function(s) for logging
    the application methods during runtime. As of
    writing this description, there is one method
    called logger that provides this functionality.

"""


with open (Path('CommandIntegrator') / 'commandintegrator.settings.json', 'r', encoding = 'utf-8') as f:
    LOG_DIR = Path(json.loads(f.read())['log_dir'])

LOG_FILE = 'runtime.log'
LOG_FILE_FULLPATH = LOG_DIR / LOG_FILE

if not os.path.isdir(LOG_DIR):
    os.mkdir(LOG_DIR)



handler = logging.FileHandler(filename = LOG_FILE_FULLPATH, encoding = 'utf-8', mode = 'w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
log = logging.getLogger('robbottherobot')
log.setLevel(logging.DEBUG)
log.addHandler(handler)

def logger(func) -> 'function':
    """
    Wrapper method for providing logging functionality.
    Use @logger to implement this method where logging
    of methods are desired.
    :param func:
        method that will be wrapped
    :returns:
        function
    """

    @functools.wraps(func)
    def inner(*args, **kwargs):
        """
        Inner method, executing the func paramter function,
        as well as executing the logger.
        :param *args:
            arbitrary parameters for the wrapped function
        :param **kwargs:
            arbitrary keyword parameters for the wrapped function
        :returns:
            Output from executed function in parameter func
        """
        try:
            results = func(*args, **kwargs)
            log.debug(f'Ran method "{func.__name__}" in {func.__module__} ' \
                      f'with ARGS: {args} & KWARGS: {kwargs} & RETURN: {results}')
            return results
        except Exception as e:
            log.error(f'Exception occured in {func.__name__}: {e}')
            raise e
    return inner


if __name__ == '__main__':
    
    @logger
    def test(a, b):
        return a + b

    @logger
    def fails(a, b):
        raise Exception('this is the error message')    

    fails(1,2)