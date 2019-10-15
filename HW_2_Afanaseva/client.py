import sys
import time
import re
import socket
import logging
import argparse
import json
import threading
from common.variables import *
from common.utils import *
from logs import client_log_config
from common.errors import IncorrectDataNotDictError, FieldMissingError, IncorrectCodeError
from decorators.decos import DecorationLogging
from metaclasses import ClientCreator

#  логирование в журнал
logger = logging.getLogger('client')
logger.setLevel(logging.DEBUG)


class Client(metaclass=ClientCreator):
    # @DecorationLogging()
    def start_client(self):
        contact = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Загружаем параметы коммандной строки
        ip_server, port_server, name_client = self.get_args()

        # Если имя пользователя не было задано, необходимо запросить пользователя.

        if not name_client:
            while True:
                name_client = input('Введите имя пользователя: ')
                if self.valid_name_client(name_client):
                    break
                else:
                    print(f'Имя должно быть словом не длиннее 25')

        # Сообщаем о запуске
        print(f'Консольный месседжер. Клиентский модуль. Добро пожаловать: {name_client}')

        logger.info(
            f'Запущен клиент с парамертами: адрес сервера: {ip_server} , порт: {port_server}, имя пользователя: {name_client}')

        try:
            contact.connect((ip_server, port_server))
        except ConnectionRefusedError:
            logger.critical('Нелязя установить соединение. Не верные даннные ip или port\n')
            exit(1)

        logger.debug(f'Установлено соединение с сервером')
        msg_to_server = self.create_presence_msg(name_client)
        logger.info(f'Сформировано сообщение серверу - {msg_to_server}')
        send_msg(contact, msg_to_server)
        logger.debug(f'Отпавлено сообщение серверу')

        try:
            answer = self.answer_server_presence(get_msg(contact))
        except json.JSONDecodeError:
            logger.error('Не удалось декодировать полученную Json строку.')
            exit(1)
        except IncorrectDataNotDictError:
            logger.error('Получен не верный формат данных\n')
            exit(1)
        except FieldMissingError as missing_error:
            logger.error(f'Нет обязательного поля - {missing_error}\n')
            exit(1)
        except IncorrectCodeError as wrong_code:
            logger.error(f'Неверный код в сообщении - {wrong_code}')
            exit(1)
        except ConnectionResetError:
            logger.critical('Не установлена связь с сервером')
        else:
            logger.info(f'Получен ответ от сервера - {answer} \n')
            print(f'Установлено соединение с сервером')

            # Запускаем взаимодействие с пользователем
            user_send = threading.Thread(target=self.user_console, args=(contact, name_client))
            user_send.daemon = True
            user_send.start()

            self.get_message_from_server(contact, name_client)

    @DecorationLogging()
    def valid_name_client(self, name_client):
        if isinstance(name_client, str) and len(name_client) < 25:
            return True
        else:
            return False

    #  обрабатываем аргументы
    @DecorationLogging()
    def get_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-ip', default=DEFAULT_IP_ADDRESS, nargs='?')
        parser.add_argument('-p', '--port', default=DEFAULT_PORT, type=int, nargs='?')
        parser.add_argument('-n', '--name', default=None, nargs='?')
        names = parser.parse_args(sys.argv[1:])
        ip_server = names.ip
        port_server = names.port
        name_client = names.name

        if not 1024 < port_server < 65535:
            logger.critical(f'Неверный port (1024 - 65535) - {port_server}\n')
            exit(1)
        elif not re.match(r'^(([1-9]?[0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.)'
                         r'{3}([1-9]?[0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$', ip_server):
            logger.critical(f'Неверный ip  - {ip_server}\n')
            exit(1)
        elif name_client:
            if not self.valid_name_client(name_client):
                logger.critical(f'Имя должно быть словом не длиннее 25 - {name_client}\n')
                exit(1)

        logger.info(f'Полученны данны ip и port сервера - {ip_server}, {port_server}')

        return ip_server, port_server, name_client

    @DecorationLogging()
    def create_presence_msg(self, account_name):
        msg = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: account_name
            }
        }
        return msg

    @DecorationLogging()
    def create_message_user(self, account_name):
        to = input('Введите имя получателя: ')
        message = input('Введите сообщение для отправки: ')
        message = {
            ACTION: MESSAGE,
            FROM: account_name,
            TO: to,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        logger.debug(f'Сформировано сообщение: {message}')
        return message

    @DecorationLogging()
    def answer_server_presence(self, msg):
        logger.debug(f'Разбор сообщения от сервера - {msg}')
        if RESPONSE in msg:
            if msg[RESPONSE] == 200:
                return 'OK: 200'
            elif msg[RESPONSE] == 400:
                return f'{msg[ERROR]}: 400'
            else:
                raise IncorrectCodeError(msg[RESPONSE])
        raise FieldMissingError(RESPONSE)

    # Функция создаёт словарь с сообщением о выходе.
    @DecorationLogging()
    def create_exit_message(self, name_client):
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: name_client
        }

    # Функция - обработчик сообщений других пользователей, поступающих с сервера.
    @DecorationLogging()
    def get_message_from_server(self, sock, my_username):
        while True:
            try:
                message = get_msg(sock)
                if ACTION in message and message[ACTION] == MESSAGE and TO in message and FROM in message \
                        and MESSAGE_TEXT in message and message[TO] == my_username:
                    print(f'\nПолучено сообщение от пользователя {message[FROM]}:\n{message[MESSAGE_TEXT]}\n')
                    logger.info(f'Получено сообщение от пользователя {message[FROM]}:\n{message[MESSAGE_TEXT]}')
                else:
                    logger.error(f'Получено некорректное сообщение с сервера: {message}')
            except IncorrectDataNotDictError:
                logger.error(f'Не удалось декодировать полученное сообщение.')
            except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                logger.critical(f'Потеряно соединение с сервером.')
                break

    @DecorationLogging()
    def help_print(self):
        print('Доступные команды:\n'
              'help - вывести подсказки по командам\n'
              'message - отправить сообщение. Кому и текст будет запрошены отдельно.\n'
              'exit - выход из программы')

    @DecorationLogging()
    # Функция взаимодействия с пользователем, запрашивает команды, отправляет сообщения
    def user_console(self, sock, name_client):
        self.help_print()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                try:
                    send_msg(sock, self.create_message_user(name_client))
                except ConnectionResetError:
                    logger.critical('Потеряно соединение с сервером.')
                    exit(1)
            elif command == 'help':
                self.help_print()
            elif command == 'exit':
                try:
                    send_msg(sock, self.create_exit_message(name_client))
                except ConnectionResetError:
                    logger.critical('Потеряно соединение с сервером.')
                    exit(1)
                print('Завершение соединения.')
                logger.info('Завершение работы по команде пользователя.')
                # Задержка неоходима, чтобы успело уйти сообщение о выходе
                time.sleep(0.5)
                break
            else:
                print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')


@DecorationLogging()
def main():
    client = Client()
    client.start_client()


if __name__ == '__main__':
    main()
