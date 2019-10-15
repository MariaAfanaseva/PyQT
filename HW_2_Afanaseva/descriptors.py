import logging
from ipaddress import ip_address
logger = logging.getLogger('server')


#  Дескриптор проверки порта
class CheckPort:
    def __set_name__(self, owner, name):
        # name = port
        self.name = name

    def __set__(self, instance, value):
        if not isinstance(value, int) or not 1024 < value < 65535:
            logger.critical('Неверные значения port (-p)')
            exit(1)
        # Если порт прошел проверку, добавляем его в список атрибутов экземпляра
        instance.__dict__[self.name] = value
        logger.info(f'Полученны данные port, который слушает сервер - {value}')


#  Дескриптор проверки адресса
class CheckIP:
    def __set_name__(self, owner, name):
        # name = IP
        self.name = name

    def __set__(self, instance, value):
        if value:
            try:
                ip_addr = str(ip_address(value))
            except ValueError:
                logger.critical('Неверные значения ip (-a)')
                exit(1)
            else:
                # Если порт прошел проверку, добавляем его в список атрибутов экземпляра
                instance.__dict__[self.name] = ip_addr
                logger.info(f'Полученны данные address, который слушает сервер - {ip_addr}')
        else:
            instance.__dict__[self.name] = value
            logger.info(f'Сервер слушает все адреса')
