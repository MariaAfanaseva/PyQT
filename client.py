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
from common.errors import IncorrectDataNotDictError, FieldMissingError, IncorrectCodeError, ServerError
from decorators.decos import DecorationLogging
from metaclasses import ClientCreator
from descriptors import CheckPort, CheckIP, CheckName
from database_client import ClientDB

#  логирование в журнал
logger = logging.getLogger('client')

#  Обьект для блокировки базы
lock_database = threading.Lock()
lock_socket = threading.Lock()


#  обрабатываем аргументы
@DecorationLogging()
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-ip', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('-p', '--port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    names = parser.parse_args(sys.argv[1:])
    ip_server = names.ip
    port_server = names.port
    name_client = names.name
    if not name_client:
        name_client = input('Введите имя логин пользователя: ')
    return ip_server, port_server, name_client


class Client(metaclass=ClientCreator):
    port_server = CheckPort()
    ip_server = CheckIP()
    name_client = CheckName()

    def __init__(self, ip_server, port_server, name_client):
        self.ip_server = ip_server
        self.port_server = port_server
        self.name_client = name_client
        self.database = ClientDB(name_client)

    def start_client(self):
        logger.debug(f'Запущена функция start_client')

        contact = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        contact.settimeout(1)
        # Сообщаем о запуске
        print(f'Консольный месседжер. Клиентский модуль. Добро пожаловать: {self.name_client}')

        logger.info(
            f'Запущен клиент с парамертами: адрес сервера: {self.ip_server} , порт: {self.port_server}, имя пользователя: {self.name_client}')

        try:
            contact.connect((self.ip_server, self.port_server))
        except ConnectionRefusedError:
            logger.critical('Нелязя установить соединение. Не верные даннные ip или port\n')
            exit(1)

        logger.debug(f'Установлено соединение с сервером')
        msg_to_server = self._create_presence_msg(self.name_client)
        logger.info(f'Сформировано сообщение серверу - {msg_to_server}')
        send_msg(contact, msg_to_server)
        logger.debug(f'Отпавлено сообщение серверу')

        try:
            answer = self._answer_server_presence(get_msg(contact))
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

            #  Загружаем данные с сервера в db client
            self._load_database(contact)

            # Запускаем взаимодействие с пользователем
            user_send = threading.Thread(target=self.user_console, args=(contact, self.name_client))
            user_send.daemon = True
            user_send.start()

            user_read = threading.Thread(target=self._get_message_from_server, args=(contact, self.name_client))
            user_read.daemon = True
            user_read.start()
            # self._get_message_from_server(contact, self.name_client)
            while True:
                time.sleep(1)
                if user_send.is_alive() and user_read.is_alive():
                    continue
                break

    @DecorationLogging()
    def _load_database(self, contact):
        # Записываем известных пользователей в базу
        try:
            users_all = self._get_users_all(contact, self.name_client)
        except ServerError:
            logger.error('Ошибка запроса списка известных пользователей.')
        else:
            self.database.add_users_known(users_all)
            print('Список известных пользователь успешно обновлен')
        # Записываем контакты
        try:
            contacts_list = self._get_contacts_all(contact, self.name_client)
        except ServerError:
            logger.error('Ошибка запроса списка контактов.')
        else:
            self.database.add_contacts(contacts_list)
            print('Список контактов успешно обновлен')

    @DecorationLogging()
    def _create_presence_msg(self, account_name):
        msg = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: account_name
            }
        }
        return msg

    @DecorationLogging()
    def _create_message_user(self, account_name):
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
    def _get_users_all(self, sock, username):
        logger.debug(f'Запрос списка известных пользователей {username}')
        request = {
            ACTION: USERS_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: username
        }
        send_msg(sock, request)
        answer = get_msg(sock)
        if RESPONSE in answer and answer[RESPONSE] == 202:
            return answer[LIST_INFO]
        else:
            raise ServerError('Неверный ответ сервера')

    @DecorationLogging()
    def _get_contacts_all(self, sock, username):
        logger.debug(f'Запрос контакт листа для пользователся {username}')
        message = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            USER: username
        }
        logger.debug(f'Сформирован запрос {message}')
        send_msg(sock, message)
        answer = get_msg(sock)
        logger.debug(f'Получен ответ {answer}')
        if RESPONSE in answer and answer[RESPONSE] == 202:
            return answer[LIST_INFO]
        else:
            raise ServerError

    @DecorationLogging()
    def _add_contact_server(self, sock, username, contact):
        logger.debug(f'Создание нового контакта {contact} у пользователя {username}')
        message = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: username,
            ACCOUNT_NAME: contact
        }
        with lock_socket:
            send_msg(sock, message)
            answer = get_msg(sock)
        if RESPONSE in answer and answer[RESPONSE] == 200:
            logging.debug(f'Удачное создание контакта {contact} у пользователя {username}')
        else:
            raise ServerError('Ошибка создания контакта')

    @DecorationLogging()
    def _del_contact_server(self, sock, username, contact):
        message = {
            ACTION: DELETE_CONTACT,
            TIME: time.time(),
            USER: username,
            ACCOUNT_NAME: contact
        }
        send_msg(sock, message)
        answer = get_msg(sock)
        if RESPONSE in answer and answer[RESPONSE] == 200:
            logging.debug(f'Удачное удаление контакта {contact} у пользователя {username}')
        else:
            raise ServerError('Ошибка удаления клиента')

    @DecorationLogging()
    def _answer_server_presence(self, msg):
        logger.debug(f'Разбор сообщения от сервера - {msg}')
        if RESPONSE in msg:
            if msg[RESPONSE] == 200:
                return 'OK: 200'
            elif msg[RESPONSE] == 400:
                raise ServerError(f'400 : {msg[ERROR]}')
            else:
                raise IncorrectCodeError(msg[RESPONSE])
        raise FieldMissingError(RESPONSE)

    # Функция создаёт словарь с сообщением о выходе.
    @DecorationLogging()
    def _create_exit_message(self, name_client):
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: name_client
        }

    # Функция - обработчик сообщений других пользователей, поступающих с сервера.
    @DecorationLogging()
    def _get_message_from_server(self, sock, my_username):
        while True:
            time.sleep(1)
            with lock_socket:
                try:
                    message = get_msg(sock)
                except IncorrectDataNotDictError:
                    logger.error(f'Не удалось декодировать полученное сообщение.')
                # Вышел таймаут соединения если errno = None, иначе обрыв соединения.
                except OSError as err:
                    # print(err.errno)
                    if err.errno:
                        logger.critical(f'Потеряно соединение с сервером.')
                        break
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                    logger.critical(f'Потеряно соединение с сервером.')
                    break
                else:
                    if ACTION in message and message[ACTION] == MESSAGE and TO in message and FROM in message \
                            and MESSAGE_TEXT in message and message[TO] == my_username:
                        print(f'\nПолучено сообщение от пользователя {message[FROM]}:\n{message[MESSAGE_TEXT]}\n')
                        logger.info(f'Получено сообщение от пользователя {message[FROM]}:\n{message[MESSAGE_TEXT]}')
                    else:
                        logger.error(f'Получено некорректное сообщение с сервера: {message}')

    @DecorationLogging()
    def _help_print(self):
        print('Доступные команды:\n'
              'users - все зарегистрированные пользователи'
              'message - отправить сообщение. Кому и текст будет запрошены отдельно.\n'
              'history - история сообщений\n'
              'contacts - список контактов\n'
              'edit - редактирование списка контактов\n'
              'help - вывести подсказки по командам\n'
              'exit - выход из программы')

    @DecorationLogging()
    # Функция взаимодействия с пользователем, запрашивает команды, отправляет сообщения
    def user_console(self, sock, name_client):
        self._help_print()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                try:
                    send_msg(sock, self._create_message_user(name_client))
                except ConnectionResetError:
                    logger.critical('Потеряно соединение с сервером.')
                    exit(1)
            elif command == 'users':
                print('Список имен все пользователей: ')
                for name in self.database.get_users_known():
                    print(name)
            elif command == 'edit':
                self._edit_contact(sock)
            elif command == 'contacts':
                for name in self.database.get_contacts():
                    print(name)
            elif command == 'help':
                self._help_print()
            elif command == 'exit':
                try:
                    send_msg(sock, self._create_exit_message(name_client))
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

    def _edit_contact(self, sock):
        act = input('Выберете действие: add - добавить контакт, del - удалить контакт: ')
        if act == 'add':
            name_contact = input('Введите имя нового контакта: ')
            if self.database.check_user(name_contact):
                with lock_database:
                    self.database.add_contact(name_contact)
                try:
                    self._add_contact_server(sock, self.name_client, name_contact)
                except ServerError:
                    logger.error('Не удалось отправить информацию на сервер.')
                except ConnectionResetError:
                    logger.error('Связь с сервером потеряна')
                else:
                    print(f'Контакт {name_contact} добавлен в список контактов')
            else:
                logger.error('Данный пользователь не зарегистрирован.')
                print('Данный пользователь не зарегистрирован.')
        elif act == 'del':
            name_contact = input('Введите имя контакта для удаления: ')
            if self.database.check_contact(name_contact):
                with lock_database:
                    self.database.del_contact(name_contact)
                with lock_socket:
                    try:
                        self._del_contact_server(sock, self.name_client, name_contact)
                    except ServerError:
                        logger.error('Не удалось отправить информацию на сервер.')
                    else:
                        print(f'Контакт {name_contact}  успешно удален')
            else:
                logger.error('Попытка удаления несуществующего контакта.')


@DecorationLogging()
def main():
    ip_server, port_server, name_client = get_args()
    client = Client(ip_server, port_server, name_client)
    client.start_client()


if __name__ == '__main__':
    main()
