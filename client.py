import sys
import os
import time
import socket
import logging
import argparse
import threading
import hashlib
import hmac
import binascii
from common.utils import *
from common.errors import IncorrectDataNotDictError, FieldMissingError, IncorrectCodeError, ServerError
from decorators.decos import DecorationLogging
from metaclasses import ClientCreator
from descriptors import CheckPort, CheckIP, CheckName
from database_client import ClientDB
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import pyqtSignal, QObject
from client.gui_start_dialog import UserNameDialog
from client.gui_main_window import ClientMainWindow
from client.gui_loading_dialog import LoadingWindow
from Cryptodome.PublicKey import RSA

logger = logging.getLogger('client')

lock_database = threading.Lock()
lock_socket = threading.Lock()


@DecorationLogging()
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-ip', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('-port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    parser.add_argument('-p', '--password', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    ip_server = namespace.ip
    port_server = namespace.port
    login_client = namespace.name
    password_client = namespace.password
    return ip_server, port_server, login_client, password_client


class Client(threading.Thread, QObject):
    port_server = CheckPort()
    ip_server = CheckIP()
    client_login = CheckName()

    # Load window signals
    connection_lack_signal = pyqtSignal()
    progressbar_signal = pyqtSignal()
    answer_server = pyqtSignal(str)

    #  Main window signals
    new_message_signal = pyqtSignal(str)
    connection_lost_signal = pyqtSignal()

    def __init__(self, ip_server, port_server, client_login,  client_password, database, key):
        self.ip_server = ip_server
        self.port_server = port_server
        self.client_login = client_login
        self.client_password = client_password
        self.database = database
        self.key = key

        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.is_connected = False

        threading.Thread.__init__(self)
        QObject.__init__(self)

    @DecorationLogging()
    def run(self):
        print(f'Console messenger. Client module. Welcome: {self.client_login}')
        logger.info(
            f'Launched client with parameters: server address: {self.ip_server} , port: {self.port_server}, username: {self.client_login}')
        # Таймаут 1 секунда, необходим для освобождения сокета
        self.connection.settimeout(1)

        for i in range(5):
            logger.info(f'Connection attempt - {i + 1}.')
            print(f'Connection attempt - {i + 1}.')
            try:
                self.connection.connect((self.ip_server, self.port_server))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                self.is_connected = True
                break
            time.sleep(1)

        if not self.is_connected:
            logger.critical('Unable to establish a connection. '
                            'Invalid ip or port or server is down.\n')
            self.connection_lack()

        logger.debug(f'Server connection established.')

        self.start_authorization_procedure()

        self.load_database()

        self.get_message_from_server(self.connection, self.client_login)

    @DecorationLogging()
    def start_authorization_procedure(self):
        pubkey = self.key.publickey().export_key().decode('ascii')
        msg_to_server = self.create_presence_msg(self.client_login, pubkey)

        logger.info(f'A message has been generated to the server - {msg_to_server}.')
        try:
            send_msg(self.connection, msg_to_server)
            logger.debug(f'Message sent to server.')

            answer_all = get_msg(self.connection)
            answer_code = self.answer_server_presence(answer_all)
            logger.info(f'Received response from server - {answer_code}.\n')

            self.send_hash_password(answer_all)

            answer_code = self.answer_server_presence(get_msg(self.connection))

        except json.JSONDecodeError:
            logger.error('Failed to decode received Json string.')
            self.connection_lack()
        except IncorrectDataNotDictError:
            logger.error('Invalid data format received.\n')
            self.connection_lack()
        except FieldMissingError as missing_error:
            logger.error(f'No required field - {missing_error}.\n')
            self.connection_lack()
        except IncorrectCodeError as wrong_code:
            logger.error(f'Invalid code in message - {wrong_code}.')
            self.connection_lack()
        except ConnectionResetError:
            logger.critical('Server connection not established.')
            self.connection_lack()
        except ServerError as er:
            logger.critical(f'{er}')
            self.is_connected = False
            self.answer_server.emit(f'{er}')
            exit(1)
        else:
            logger.info(f'Received response from server - {answer_code}.\n')
            print(f'Server connection established.')
            self.progressbar_signal.emit()

    @DecorationLogging()
    def get_hash_password(self):
        password_bytes = self.client_password.encode('utf-8')
        salt = self.client_login.lower().encode('utf-8')
        password_hash = hashlib.pbkdf2_hmac('sha512', password_bytes, salt, 10000)
        password_hash_string = binascii.hexlify(password_hash)
        return password_hash_string

    @DecorationLogging()
    def send_hash_password(self, answer_all):
        answer_data = answer_all[DATA]
        password_hash_string = self.get_hash_password()

        hash = hmac.new(password_hash_string, answer_data.encode('utf-8'))
        digest = hash.digest()
        my_answer = RESPONSE_511
        my_answer[DATA] = binascii.b2a_base64(digest).decode('ascii')

        send_msg(self.connection, my_answer)

    @DecorationLogging()
    def connection_lack(self):
        self.is_connected = False
        self.connection_lack_signal.emit()
        exit(1)

    @DecorationLogging()
    def load_database(self):
        try:
            users_all = self.get_users_all()
        except (ConnectionResetError, ServerError):
            logger.error('Error requesting list of known users.')
            self.connection_lack()
        else:
            self.database.add_users_known(users_all)
            print('List of known users updated successfully.')
            self.progressbar_signal.emit()
        try:
            contacts_list = self.get_contacts_all()
        except (ConnectionResetError, ServerError):
            logger.error('Contact list request error.')
            self.connection_lack()
        else:
            self.database.add_contacts(contacts_list)
            print('Contact list updated successfully.')
            self.progressbar_signal.emit()

    @DecorationLogging()
    def create_presence_msg(self, account_name, pubkey):
        msg = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: account_name,
                PUBLIC_KEY: pubkey
            }
        }
        return msg

    @DecorationLogging()
    def get_users_all(self):
        logger.debug(f'Request a list of known users {self.client_login}')
        request = {
            ACTION: USERS_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: self.client_login
        }
        send_msg(self.connection, request)
        answer = get_msg(self.connection)
        if RESPONSE in answer and answer[RESPONSE] == 202:
            return answer[LIST_INFO]
        else:
            raise ServerError('Invalid server response.')

    @DecorationLogging()
    def get_contacts_all(self):
        logger.debug(f'Request contact sheet for user {self.client_login}.')
        message = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            USER: self.client_login
        }
        logger.debug(f'Formed request {message}')
        send_msg(self.connection, message)
        answer = get_msg(self.connection)
        logger.debug(f'Answer received {answer}')
        if RESPONSE in answer and answer[RESPONSE] == 202:
            return answer[LIST_INFO]
        else:
            raise ServerError

    @DecorationLogging()
    def answer_server_presence(self, msg):
        logger.debug(f'Parsing a message from the server - {msg}')
        if RESPONSE in msg:
            if msg[RESPONSE] == 511:
                return 'OK: 511'
            elif msg[RESPONSE] == 200:
                return 'OK: 200'
            elif msg[RESPONSE] == 400:
                logger.info(f'ERROR 400: {msg[ERROR]}')
                raise ServerError(f'{msg[ERROR]}')
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
                    logger.error(f'Failed to decode received message.')
                # Вышел таймаут соединения если errno = None, иначе обрыв соединения.
                except OSError as err:
                    # print(err.errno)
                    if err.errno:
                        logger.critical(f'Lost server connection.')
                        self.connection_lost_signal.emit()
                        break
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                    logger.critical(f'Lost server connection.')
                    self.connection_lost_signal.emit()
                    break
                else:
                    if ACTION in message and message[ACTION] == MESSAGE and TO in message and FROM in message \
                            and MESSAGE_TEXT in message and message[TO] == my_username:
                        print(f'\nReceived message from user{message[FROM]}:\n{message[MESSAGE_TEXT]}.\n')
                        logger.info(f'Received message from user {message[FROM]}:\n{message[MESSAGE_TEXT]}.')
                        self.database.save_message(message[FROM], 'in', message[MESSAGE_TEXT])
                        self.new_message_signal.emit(message[FROM])
                    else:
                        logger.error(f'Invalid message received from server: {message}')

    @DecorationLogging()
    def send_user_message(self, contact_name, message):
        message = {
            ACTION: MESSAGE,
            FROM: self.client_login,
            TO: contact_name,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        with lock_socket:
            try:
                send_msg(self.connection, message)
                answer = get_msg(self.connection)
            except (ConnectionResetError, ConnectionAbortedError, OSError):
                logger.critical('Lost server connection.')
                return False
            else:
                if answer[RESPONSE] == 400:
                    logger.info(f'{answer[ERROR]}. User {contact_name} is offline.')
                    return f'User {contact_name} is offline!'
        logger.debug(f'Message sent: {message},from {self.client_login} username {contact_name}')
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
                logger.error('Failed to send information to server.')
            except ConnectionResetError:
                logger.error('Server connection lost.')
            else:
                logger.info(f'New contact added {new_contact_name} at the user {self.client_login}.')
                return True
        else:
            logger.error('This user is not registered.')

    @DecorationLogging()
    def add_contact_server(self, new_contact_name):
        logger.debug(f'Create a new contact {new_contact_name} at the user {self.client_login}.')
        message = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.client_login,
            ACCOUNT_NAME: new_contact_name
        }
        with lock_socket:
            send_msg(self.connection, message)
            answer = get_msg(self.connection)
        if RESPONSE in answer and answer[RESPONSE] == 200:
            logging.debug(f'Successful contact creation {new_contact_name} at the user {self.client_login}.')
        else:
            raise ServerError('Error creating contact.')

    @DecorationLogging()
    def del_contact(self, del_contact_name):
        if self.database.is_contact(del_contact_name):
            with lock_database:
                self.database.del_contact(del_contact_name)
            try:
                self.del_contact_server(del_contact_name)
            except ServerError:
                logger.error('Failed to send information to server.')
            else:
                print(f'Contact {del_contact_name} successfully deleted.')
                return True
        else:
            logger.info('Attempt to delete a nonexistent contact.')

    @DecorationLogging()
    def del_contact_server(self, del_contact_name):
        message = {
            ACTION: DELETE_CONTACT,
            TIME: time.time(),
            USER: self.client_login,
            ACCOUNT_NAME: del_contact_name
        }
        with lock_socket:
            send_msg(self.connection, message)
            answer = get_msg(self.connection)
        if RESPONSE in answer and answer[RESPONSE] == 200:
            logging.debug(f'Successfully delete a contact {del_contact_name} at the user {self.client_login}')
        else:
            raise ServerError('Client uninstall error.')

    @DecorationLogging()
    def exit_client(self):
        try:
            send_msg(self.connection, self.create_exit_message(self.client_login))
        except ConnectionResetError:
            logger.critical('Lost server connection.')
            exit(1)
        logger.info('Application shutdown by user command\n.')
        print('Application shutdown by user command.')

    @DecorationLogging()
    def create_exit_message(self, client_login):
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: client_login
        }


@DecorationLogging()
def start_dialog(app, client_login, client_password):
    if not client_login or not client_password:
        dialog = UserNameDialog(app)
        dialog.init_ui()
        app.exec_()
        if dialog.ok_clicked:
            client_login = dialog.login_edit.text()
            client_password = dialog.password_edit.text()
            return client_login, client_password
        else:
            exit(0)
    else:
        return client_login, client_password


@DecorationLogging()
def get_key(client_login):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, f'{client_login}.key')
    if not os.path.exists(file_path):
        key = RSA.generate(2048, os.urandom)
        with open(file_path, 'wb') as file:
            file.write(key.export_key())
    else:
        with open(file_path, 'rb') as file:
            key = RSA.import_key(file.read())
    return key


@DecorationLogging()
def loading_window(app, client_transport):
    loading = LoadingWindow(app)
    loading.init_ui()
    loading.make_connection_with_signals(client_transport)
    app.exec_()


@DecorationLogging()
def main():
    app = QApplication(sys.argv)
    ip_server, port_server, client_login, client_password = get_args()
    client_login, client_password = start_dialog(app, client_login, client_password)

    database = ClientDB(client_login)

    key = get_key(client_login)

    client_transport = Client(ip_server, port_server, client_login, client_password, database, key)
    client_transport.daemon = True
    client_transport.start()

    #  Loading window
    loading_window(app, client_transport)
    
    if client_transport.is_connected:
        main_window = ClientMainWindow(app, client_transport, database)
        main_window.init_ui()
        main_window.make_connection_with_signals(client_transport)
        main_window.setWindowTitle(f'Chat program. User - {client_login}')
        app.exec_()

        client_transport.exit_client()


if __name__ == '__main__':
    main()
