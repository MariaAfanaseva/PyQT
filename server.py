import socket
import sys
import logging
import argparse
import select
import time
import threading
from common.variables import *
from common.utils import *
from logs import server_log_config
from common.errors import IncorrectDataNotDictError
from decorators.decos import DecorationLogging
from descriptors import CheckPort, CheckIP
from metaclasses import ServerCreator
from database_server import ServerDB
from PyQt5.QtWidgets import QApplication

logger = logging.getLogger('server')
logger.setLevel(logging.DEBUG)


#  Получаем аргументы при запуске файла
@DecorationLogging()
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default=DEFAULT_PORT, type=int)
    parser.add_argument('-a', '--addr', default='')
    names = parser.parse_args(sys.argv[1:])
    address = names.addr
    port = names.port
    return address, port


class Server(metaclass=ServerCreator):
    # Дескрипторы праверки порта и адреса
    listen_port = CheckPort()
    listen_ip = CheckIP()

    def __init__(self, listen_ip, listen_port, database):
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.database = database
        #  Все клиенты
        self.clients = []
        #  Все сообщения
        self.messages = []
        #  Имена подключенных клиентов
        self.names = dict()

    def socket_init(self):
        # Создаем сокет
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Готовим сокет
        connection.bind((self.listen_ip, self.listen_port))
        connection.settimeout(0.5)
        connection.listen(MAX_CONNECTIONS)  # Слушаем порт

        self.connection = connection

    @DecorationLogging()
    def print_help(self):
        print('Поддерживаемые комманды:\n'
              'users - список известных пользователей\n'
              'connected - список подключенных пользователей\n'
              'history - история входов пользователя\n'
              'exit - завершение работы сервера.\n'
              'help - вывод справки по поддерживаемым командам')

    @DecorationLogging()
    def get_information(self):
        time.sleep(1)
        self.print_help()
        while True:
            command = input('Введите комманду: ')
            if command == 'help':
                self.print_help()
            elif command == 'exit':
                break
            elif command == 'users':
                for user in sorted(self.database.users_all()):
                    print(f'Пользователь с логином {user[0]}, последний вход: {user[2]}')
            elif command == 'connected':
                for user in sorted(self.database.users_active_list()):
                    print(f'Пользователь с логином {user[0]}, подключен ip - {user[1]} port - {user[2]}, '
                          f'время установки соединения: {user[3]}')
            elif command == 'history':
                login = input(
                    'Введите логин пользователя для просмотра истории. Для вывода всей истории, просто нажмите Enter: ')
                for user in sorted(self.database.history_login(login)):
                    print(f'Пользователь: {user[0]} время входа: {user[3]}. Вход с: ip - {user[1]} port - {user[2]}')
            else:
                print('Команда не распознана.')

    @DecorationLogging()
    def start_server(self):
        # Вывод информации на сервере в отденьном потоке
        server_info = threading.Thread(target=self.get_information)
        server_info.daemon = True
        server_info.start()

        # Инициализация Сокета
        self.socket_init()
        # Основной цикл программы сервера
        # Ждём подключения, если таймаут вышел, ловим исключение.
        while True:
            try:
                client, client_address = self.connection.accept()
            except OSError:
                pass
            else:
                logger.info(f'Установлено соединение с клиетом - {client_address}')
                self.clients.append(client)

            clients_read_lst = []
            clients_send_lst = []
            err_lst = []

            try:
                if self.clients:
                    clients_read_lst, clients_send_lst, err_lst = select.select(self.clients, self.clients, [], 0)
            except OSError as err:
                logger.error(f'Ошибка работы с сокетами: {err}')

            #  Получаем сообщение от клиентов
            if clients_read_lst:
                for client in clients_read_lst:
                    try:
                        message =get_msg(client)
                    except IncorrectDataNotDictError:
                        logger.error('Получен не верный формат данных')
                    except (ConnectionResetError, json.decoder.JSONDecodeError):
                        logger.info(f'Клиент {client.getpeername()} отключился от сервера.')
                        for name in self.names:
                            if self.names[name] == client:
                                self.database.user_logout(name)
                                del self.names[name]
                                break
                        client.close()
                        self.clients.remove(client)
                    else:
                        logger.debug(f'Получено сообщение от клиента {message}')
                        self.client_msg(message, self.messages, client, self.names, self.clients)

            # Если есть сообщения для отправки и ожидающие клиенты, отправляем им сообщение.
            if self.messages:
                for msg in self.messages:
                    try:
                        self.send_messages_users(self.names, clients_send_lst, msg)
                    except (ConnectionResetError, ConnectionError):
                        logger.info(f'Связь с клиентом с именем {msg[TO]} была потеряна')
                        self.clients.remove(self.names[msg[TO]])
                        del self.names[msg[TO]]
                        self.database.user_logout(msg[TO])
                self.messages.clear()

    #  Разбираем входящие сообщения
    @DecorationLogging()
    def client_msg(self, message, messages_lst, client, names, clients):
        logger.debug(f'Разбор сообщения от клиента - {message}')

        #  Разбор сообщения RESPONSE от клиента
        if ACTION in message and TIME in message and USER in message \
                and ACCOUNT_NAME in message[USER] and message[ACTION] == PRESENCE:
            #  Добавляем нового клиента в список names
            if message[USER][ACCOUNT_NAME] not in names.keys():
                names[message[USER][ACCOUNT_NAME]] = client
                msg = {RESPONSE: 200}
                send_msg(client, msg)
                logger.debug(f'Отправлен ответ клиенту - {msg} \n')
                client_ip, client_port = client.getpeername()
                self.database.login_user(message[USER][ACCOUNT_NAME], client_ip, client_port)
            else:
                msg = {
                    RESPONSE: 400,
                    ERROR: 'Wrong name'
                }
                send_msg(client, msg)
                logger.debug(f'Имя пользователя уже занято. Отправлен ответ клиенту - {msg} \n')
                clients.remove(client)
                client.close()

        #  Добавляем сообщение в список сообщений
        elif ACTION in message and message[ACTION] == MESSAGE and\
                TIME in message and MESSAGE_TEXT in message and TO in message and FROM in message:
            messages_lst.append(message)

        elif ACTION in message and message[ACTION] == GET_CONTACTS and USER in message \
                and names[message[USER]] == client:
            answer = {
                RESPONSE: 202,
                LIST_INFO: self.database.get_contacts(message[USER])
                }
            send_msg(client, answer)
            logger.debug(f'Отправлен список контактов - {answer[LIST_INFO]} клиенту - {message[USER]}\n')

        elif ACTION in message and message[ACTION] == ADD_CONTACT \
                and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.add_contact(message[USER], message[ACCOUNT_NAME])
            send_msg(client, {RESPONSE: 200})
            logger.debug(f'Добавлен новый контакт {message[ACCOUNT_NAME]} у пользователя {message[USER]}')

        elif ACTION in message and message[ACTION] == DELETE_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.delete_contact(message[USER], message[ACCOUNT_NAME])
            send_msg(client, {RESPONSE: 200})
            logger.debug(f'Удален контакт {message[ACCOUNT_NAME]} у пользователя {message[USER]}')


        # Если это запрос известных пользователей
        elif ACTION in message and message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            answer = {
                RESPONSE: 202,
                LIST_INFO: [user[0] for user in self.database.users_all()]
            }
            send_msg(client, answer)

        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            logger.info(f'Пользователь {message[ACCOUNT_NAME]} отключился')
            user_name = message[ACCOUNT_NAME]
            self.database.user_logout(user_name)
            clients.remove(names[user_name])
            names[user_name].close()
            del names[user_name]

        else:
            msg = {
                RESPONSE: 400,
                ERROR: 'Bad Request'
            }
            send_msg(client, msg)
            logger.info(f'Отправлены ошибки клиенту - {msg} \n')

    #  Отвечаем пользователям
    @DecorationLogging()
    def send_messages_users(self, names, clients_send_lst, msg):
        if msg[TO] in names and names[msg[TO]] in clients_send_lst:
            send_msg(names[msg[TO]], msg)
            self.database.sending_message(msg[FROM], msg[TO])
            logger.info(f'Отправлено сообщение пользователю {msg[TO]} от пользователя {msg[FROM]}.')
        elif msg[TO] in names and names[msg[TO]] not in clients_send_lst:
            raise ConnectionError
        else:
            logger.error(
                f'Пользователь {msg[TO]} не зарегистрирован на сервере, отправка сообщения невозможна.')


@DecorationLogging()
def main():
    listen_ip, listen_port = get_args()
    database = ServerDB()
    server = Server(listen_ip, listen_port, database)
    server.start_server()


if __name__ == '__main__':
    main()