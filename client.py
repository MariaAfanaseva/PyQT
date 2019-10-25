import sys
import time
import socket
import logging
import argparse
import threading
from common.utils import *
from common.errors import IncorrectDataNotDictError, FieldMissingError, IncorrectCodeError, ServerError
from decorators.decos import DecorationLogging
from metaclasses import ClientCreator
from descriptors import CheckPort, CheckIP, CheckName
from database_client import ClientDB
from PyQt5.QtWidgets import QApplication
from client.gui_start_dialog import UserNameDialog
from client.gui_main_window import ClientMainWindow

logger = logging.getLogger('client')

lock_database = threading.Lock()
lock_socket = threading.Lock()


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
    return ip_server, port_server, name_client


class Client(threading.Thread, metaclass=ClientCreator):
    port_server = CheckPort()
    ip_server = CheckIP()
    name_client = CheckName()

    def __init__(self, ip_server, port_server, name_client, database):
        self.ip_server = ip_server
        self.port_server = port_server
        self.name_client = name_client
        self.database = database
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        super().__init__()

        print(f'Консольный месседжер. Клиентский модуль. Добро пожаловать: {self.name_client}')
        logger.info(
            f'Запущен клиент с парамертами: адрес сервера: {self.ip_server} , порт: {self.port_server}, имя пользователя: {self.name_client}')
        try:
            # Таймаут 1 секунда, необходим для освобождения сокета
            self.connection.settimeout(1)
            self.connection.connect((self.ip_server, self.port_server))
        except ConnectionRefusedError:
            logger.critical('Нелязя установить соединение. Не верные даннные ip или port\n')
            exit(1)

        logger.debug(f'Установлено соединение с сервером')
        msg_to_server = self.create_presence_msg(self.name_client)
        logger.info(f'Сформировано сообщение серверу - {msg_to_server}')
        send_msg(self.connection, msg_to_server)
        logger.debug(f'Отпавлено сообщение серверу')

        try:
            answer = self.answer_server_presence(get_msg(self.connection))
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
            self.load_database()

    @DecorationLogging()
    def run(self):
        self.get_message_from_server(self.connection, self.name_client)

    @DecorationLogging()
    def load_database(self):
        try:
            users_all = self.get_users_all()
        except ServerError:
            logger.error('Ошибка запроса списка известных пользователей.')
        else:
            self.database.add_users_known(users_all)
            print('Список известных пользователь успешно обновлен')
        try:
            contacts_list = self.get_contacts_all()
        except ServerError:
            logger.error('Ошибка запроса списка контактов.')
        else:
            self.database.add_contacts(contacts_list)
            print('Список контактов успешно обновлен')

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
    def get_users_all(self):
        logger.debug(f'Запрос списка известных пользователей {self.name_client}')
        request = {
            ACTION: USERS_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: self.name_client
        }
        send_msg(self.connection, request)
        answer = get_msg(self.connection)
        if RESPONSE in answer and answer[RESPONSE] == 202:
            return answer[LIST_INFO]
        else:
            raise ServerError('Неверный ответ сервера')

    @DecorationLogging()
    def get_contacts_all(self):
        logger.debug(f'Запрос контакт листа для пользователся {self.name_client}')
        message = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            USER: self.name_client
        }
        logger.debug(f'Сформирован запрос {message}')
        send_msg(self.connection, message)
        answer = get_msg(self.connection)
        logger.debug(f'Получен ответ {answer}')
        if RESPONSE in answer and answer[RESPONSE] == 202:
            return answer[LIST_INFO]
        else:
            raise ServerError

    @DecorationLogging()
    def answer_server_presence(self, msg):
        logger.debug(f'Разбор сообщения от сервера - {msg}')
        if RESPONSE in msg:
            if msg[RESPONSE] == 200:
                return 'OK: 200'
            elif msg[RESPONSE] == 400:
                raise ServerError(f'400 : {msg[ERROR]}')
            else:
                raise IncorrectCodeError(msg[RESPONSE])
        raise FieldMissingError(RESPONSE)

    @DecorationLogging()
    def get_message_from_server(self, sock, my_username):
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
                        self.database.save_message(message[FROM], 'in', message[MESSAGE_TEXT])
                    else:
                        logger.error(f'Получено некорректное сообщение с сервера: {message}')

    @DecorationLogging()
    def send_user_message(self, contact_name, message):
        message = {
            ACTION: MESSAGE,
            FROM: self.name_client,
            TO: contact_name,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        with lock_socket:
            try:
                send_msg(self.connection, message)
                answer = get_msg(self.connection)
            except (ConnectionResetError, ConnectionAbortedError, OSError):
                logger.critical('Потеряно соединение с сервером.')
                return False
            else:
                if answer[RESPONSE] == 400:
                    logger.info(f'{answer[ERROR]}. Пользователя {contact_name} нет в сети')
                    return f'User {contact_name} is offline!'
        logger.debug(f'Отправлено сообщение: {message},от {self.name_client} пользователю {contact_name}')
        self.database.save_message(message[TO], 'out', message[MESSAGE_TEXT])
        return True

    @DecorationLogging()
    def add_contact(self, new_contact_name):
        if self.database.is_user(new_contact_name):
            with lock_database:
                self.database.add_contact(new_contact_name)
            try:
                self.add_contact_server(new_contact_name)
            except ServerError:
                logger.error('Не удалось отправить информацию на сервер.')
            except ConnectionResetError:
                logger.error('Связь с сервером потеряна')
            else:
                logger.info(f'Добавлен новый контакт {new_contact_name} у пользователя {self.name_client}')
                return True
        else:
            logger.error('Данный пользователь не зарегистрирован.')

    @DecorationLogging()
    def add_contact_server(self, new_contact_name):
        logger.debug(f'Создание нового контакта {new_contact_name} у пользователя {self.name_client}')
        message = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.name_client,
            ACCOUNT_NAME: new_contact_name
        }
        with lock_socket:
            send_msg(self.connection, message)
            answer = get_msg(self.connection)
        if RESPONSE in answer and answer[RESPONSE] == 200:
            logging.debug(f'Удачное создание контакта {new_contact_name} у пользователя {self.name_client}')
        else:
            raise ServerError('Ошибка создания контакта')

    @DecorationLogging()
    def del_contact(self, del_contact_name):
        if self.database.is_contact(del_contact_name):
            with lock_database:
                self.database.del_contact(del_contact_name)
            try:
                self.del_contact_server(del_contact_name)
            except ServerError:
                logger.error('Не удалось отправить информацию на сервер.')
            else:
                print(f'Контакт {del_contact_name}  успешно удален')
                return True
        else:
            logger.info('Попытка удаления несуществующего контакта.')

    @DecorationLogging()
    def del_contact_server(self, del_contact_name):
        message = {
            ACTION: DELETE_CONTACT,
            TIME: time.time(),
            USER: self.name_client,
            ACCOUNT_NAME: del_contact_name
        }
        with lock_socket:
            send_msg(self.connection, message)
            answer = get_msg(self.connection)
        if RESPONSE in answer and answer[RESPONSE] == 200:
            logging.debug(f'Удачное удаление контакта {del_contact_name} у пользователя {self.name_client}')
        else:
            raise ServerError('Ошибка удаления клиента')

    @DecorationLogging()
    def exit_client(self):
        try:
            send_msg(self.connection, self.create_exit_message(self.name_client))
        except ConnectionResetError:
            logger.critical('Потеряно соединение с сервером.')
            exit(1)
        logger.info('Завершение работы по команде пользователя\n.')
        print('Завершение работы по команде пользователя.')

    @DecorationLogging()
    def create_exit_message(self, name_client):
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: name_client
        }


@DecorationLogging()
def start_dialog(app, client_name):
    if not client_name:
        dialog = UserNameDialog(app)
        dialog.init_ui()
        app.exec_()
        if dialog.ok_clicked:
            client_name = dialog.name_edit.text()
            return client_name
        else:
            exit(0)
    else:
        return client_name


@DecorationLogging()
def main():
    app = QApplication(sys.argv)
    ip_server, port_server, client_name = get_args()
    client_name = start_dialog(app, client_name)

    database = ClientDB(client_name)

    client_transport = Client(ip_server, port_server, client_name, database)
    client_transport.daemon = True
    client_transport.start()

    #  Запускаем главное окно
    main_window = ClientMainWindow(app, client_transport, database)
    main_window.init_ui()
    main_window.setWindowTitle(f'Chat program. User - {client_name}')
    app.exec_()

    client_transport.exit_client()


if __name__ == '__main__':
    main()
