import logging
import sys
import os
sys.path.append(os.path.join(os.getcwd(), '..'))
import logs.client_log_config
import logs.server_log_config

if sys.argv[0].find('server') == -1:
    log = logging.getLogger('client')
else:
    log = logging.getLogger('server')


class DecorationLogging:
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            log.debug(f'Запущена функция {func.__name__}, из модуля {func.__module__}, с параметрами {args}, {kwargs}')
            result = func(*args, **kwargs)
            return result
        return wrapper

