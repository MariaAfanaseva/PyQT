import sys
import time
import socket
import logging
import argparse
import threading
import hashlib
import hmac
import binascii
import json
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import pyqtSignal, QObject
from common.utils import get_msg, send_msg
from common.variables import DEFAULT_IP_ADDRESS, DEFAULT_PORT,  TO, USER, ACCOUNT_NAME, \
    RESPONSE_511, ERROR, DATA, RESPONSE, TIME, PRESENCE, FROM, \
    EXIT, GET_CONTACTS, PUBLIC_KEY, ACTION, MESSAGE_TEXT, MESSAGE, LIST_INFO, ADD_CONTACT, \
    DELETE_CONTACT, USERS_REQUEST, PUBLIC_KEY_REQUEST
from common.errors import IncorrectDataNotDictError, FieldMissingError, IncorrectCodeError, ServerError
from decorators.decos import Logging
from common.descriptors import CheckPort, CheckIP, CheckName
from client.database_client import ClientDB
from client.gui_client.gui_start_dialog import UserNameDialog
from client.gui_client.gui_main_window import ClientMainWindow
from client.gui_client.gui_loading_dialog import LoadingWindow
from client.encrypt_decrypt import EncryptDecrypt

LOGGER = logging.getLogger('client')

LOCK_DATABASE = threading.Lock()
LOCK_SOCKET = threading.Lock()


@Logging()
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

    def __init__(self, ip_server, port_server, client_login, client_password, database, encrypt_decrypt):
        self.ip_server = ip_server
        self.port_server = port_server
        self.client_login = client_login
        self.client_password = client_password
        self.database = database
        self.encrypt_decrypt = encrypt_decrypt
        self.pubkey = self.encrypt_decrypt.get_pubkey_user()

        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.is_connected = False

        threading.Thread.__init__(self)
        QObject.__init__(self)

    @Logging()
    def run(self):
        print(f'Console messenger. Client module. Welcome: {self.client_login}')
        LOGGER.info(
            f'Launched client with parameters: server address: {self.ip_server} ,'
            f' port: {self.port_server}, username: {self.client_login}')
        # Timeout 1 second needed to free socket
        self.connection.settimeout(1)

        for i in range(5):
            LOGGER.info(f'Connection attempt - {i + 1}.')
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
            LOGGER.critical('Unable to establish a connection. '
                            'Invalid ip or port or server is down.\n')
            self.connection_lack()

        LOGGER.debug(f'Server connection established.')

        self.start_authorization_procedure()

        self.load_database()

        self.get_message_from_server(self.connection, self.client_login)

    @Logging()
    def start_authorization_procedure(self):
        pubkey = self.pubkey.decode('ascii')
        msg_to_server = self.create_presence_msg(self.client_login, pubkey)

        LOGGER.info(f'A message has been generated to the server - {msg_to_server}.')
        try:
            send_msg(self.connection, msg_to_server)
            LOGGER.debug(f'Message sent to server.')

            answer_all = get_msg(self.connection)
            answer_code = self.answer_server_presence(answer_all)
            LOGGER.info(f'Received response from server - {answer_code}.\n')

            self.send_hash_password(answer_all)

            answer_code = self.answer_server_presence(get_msg(self.connection))

        except json.JSONDecodeError:
            LOGGER.error('Failed to decode received Json string.')
            self.connection_lack()
        except IncorrectDataNotDictError:
            LOGGER.error('Invalid data format received.\n')
            self.connection_lack()
        except FieldMissingError as missing_error:
            LOGGER.error(f'No required field - {missing_error}.\n')
            self.connection_lack()
        except IncorrectCodeError as wrong_code:
            LOGGER.error(f'Invalid code in message - {wrong_code}.')
            self.connection_lack()
        except ConnectionResetError:
            LOGGER.critical('Server connection not established.')
            self.connection_lack()
        except ServerError as er:
            LOGGER.critical(f'{er}')
            self.is_connected = False
            self.answer_server.emit(f'{er}')
            exit(1)
        else:
            LOGGER.info(f'Received response from server - {answer_code}.\n')
            print(f'Server connection established.')
            self.progressbar_signal.emit()

    @Logging()
    def get_hash_password(self):
        password_bytes = self.client_password.encode('utf-8')
        salt = self.client_login.lower().encode('utf-8')
        password_hash = hashlib.pbkdf2_hmac('sha512', password_bytes, salt, 10000)
        password_hash_string = binascii.hexlify(password_hash)
        return password_hash_string

    @Logging()
    def send_hash_password(self, answer_all):
        answer_data = answer_all[DATA]
        password_hash_string = self.get_hash_password()

        hash = hmac.new(password_hash_string, answer_data.encode('utf-8'))
        digest = hash.digest()
        my_answer = RESPONSE_511
        my_answer[DATA] = binascii.b2a_base64(digest).decode('ascii')

        send_msg(self.connection, my_answer)

    @Logging()
    def connection_lack(self):
        self.is_connected = False
        self.connection_lack_signal.emit()
        exit(1)

    @Logging()
    def load_database(self):
        try:
            users_all = self.get_users_all()
        except (ConnectionResetError, ServerError):
            LOGGER.error('Error requesting list of known users.')
            self.connection_lack()
        else:
            self.database.add_users_known(users_all)
            print('List of known users updated successfully.')
            self.progressbar_signal.emit()
        try:
            contacts_list = self.get_contacts_all()
        except (ConnectionResetError, ServerError):
            LOGGER.error('Contact list request error.')
            self.connection_lack()
        else:
            self.database.add_contacts(contacts_list)
            print('Contact list updated successfully.')
            self.progressbar_signal.emit()

    @Logging()
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

    @Logging()
    def get_users_all(self):
        LOGGER.debug(f'Request a list of known users {self.client_login}')
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

    @Logging()
    def get_contacts_all(self):
        LOGGER.debug(f'Request contact sheet for user {self.client_login}.')
        message = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            USER: self.client_login
        }
        LOGGER.debug(f'Formed request {message}')
        send_msg(self.connection, message)
        answer = get_msg(self.connection)
        LOGGER.debug(f'Answer received {answer}')
        if RESPONSE in answer and answer[RESPONSE] == 202:
            return answer[LIST_INFO]
        else:
            raise ServerError

    @Logging()
    def answer_server_presence(self, msg):
        LOGGER.debug(f'Parsing a message from the server - {msg}')
        if RESPONSE in msg:
            if msg[RESPONSE] == 511:
                return 'OK: 511'
            elif msg[RESPONSE] == 200:
                return 'OK: 200'
            elif msg[RESPONSE] == 400:
                LOGGER.info(f'ERROR 400: {msg[ERROR]}')
                raise ServerError(f'{msg[ERROR]}')
            else:
                raise IncorrectCodeError(msg[RESPONSE])
        raise FieldMissingError(RESPONSE)

    @Logging()
    def is_received_pubkey(self, login):
        current_chat_key = self.pubkey_request(login)
        if current_chat_key:
            self.encrypt_decrypt.create_current_encrypt(current_chat_key)
            return True
        return False

    @Logging()
    def pubkey_request(self, login):
        """The function of requesting the public key of the client from the server."""
        LOGGER.debug(f'Public key request for {login}')
        request = {
            ACTION: PUBLIC_KEY_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: login
        }
        with LOCK_SOCKET:
            try:
                send_msg(self.connection, request)
                answer = get_msg(self.connection)
            except (OSError, json.JSONDecodeError):
                self.connection_lost_signal.emit()
                return
        if RESPONSE in answer and answer[RESPONSE] == 511:
            LOGGER.debug(f'Loaded public key for {login}')
            return answer[DATA]
        else:
            LOGGER.error(f'Failed to get the key of the interlocutor {login}. '
                         f'Answer server {answer}')

    @Logging()
    def get_message_from_server(self, sock, my_username):
        while True:
            time.sleep(1)
            with LOCK_SOCKET:
                try:
                    message = get_msg(sock)
                except IncorrectDataNotDictError:
                    LOGGER.error(f'Failed to decode received message.')
                # Connection timed out if errno = None, otherwise connection break.
                except OSError as err:
                    # print(err.errno)
                    if err.errno:
                        LOGGER.critical(f'Lost server connection.')
                        self.connection_lost_signal.emit()
                        break
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                    LOGGER.critical(f'Lost server connection.')
                    self.connection_lost_signal.emit()
                    break
                else:
                    if ACTION in message and message[ACTION] == MESSAGE and TO in message and FROM in message \
                            and MESSAGE_TEXT in message and message[TO] == my_username:

                        user_login = message[FROM]
                        decrypted_message = self.encrypt_decrypt.message_decryption(message[MESSAGE_TEXT])

                        print(f'\nReceived message from user{user_login}:\n{decrypted_message}.\n')
                        LOGGER.info(f'Received message from user {user_login}:\n{decrypted_message}.')
                        self.database.save_message(user_login, 'in', decrypted_message)
                        self.new_message_signal.emit(user_login)
                    else:
                        LOGGER.error(f'Invalid message received from server: {message}')

    @Logging()
    def send_user_message(self, contact_name, message_text):
        encrypted_message = self.encrypt_decrypt.message_encryption(message_text)
        message = {
            ACTION: MESSAGE,
            FROM: self.client_login,
            TO: contact_name,
            TIME: time.time(),
            MESSAGE_TEXT: encrypted_message
        }
        with LOCK_SOCKET:
            try:
                send_msg(self.connection, message)
                answer = get_msg(self.connection)
            except (ConnectionResetError, ConnectionAbortedError, OSError):
                LOGGER.critical('Lost server connection.')
                return False
            else:
                if answer[RESPONSE] == 400:
                    LOGGER.info(f'{answer[ERROR]}. User {contact_name} is offline.')
                    return f'User {contact_name} is offline!'
        LOGGER.debug(f'Message sent: {message},from {self.client_login} username {contact_name}')
        self.database.save_message(contact_name, 'out', message_text)
        return True

    @Logging()
    def add_contact(self, new_contact_name):
        if self.database.is_user(new_contact_name):
            with LOCK_DATABASE:
                self.database.add_contact(new_contact_name)
            try:
                self.add_contact_server(new_contact_name)
            except ServerError:
                LOGGER.error('Failed to send information to server.')
            except ConnectionResetError:
                LOGGER.error('Server connection lost.')
            else:
                LOGGER.info(f'New contact added {new_contact_name} at the user {self.client_login}.')
                return True
        else:
            LOGGER.error('This user is not registered.')

    @Logging()
    def add_contact_server(self, new_contact_name):
        LOGGER.debug(f'Create a new contact {new_contact_name} at the user {self.client_login}.')
        message = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.client_login,
            ACCOUNT_NAME: new_contact_name
        }
        with LOCK_SOCKET:
            send_msg(self.connection, message)
            answer = get_msg(self.connection)
        if RESPONSE in answer and answer[RESPONSE] == 200:
            logging.debug(f'Successful contact creation {new_contact_name} at the user {self.client_login}.')
        else:
            raise ServerError('Error creating contact.')

    @Logging()
    def del_contact(self, del_contact_name):
        if self.database.is_contact(del_contact_name):
            with LOCK_DATABASE:
                self.database.del_contact(del_contact_name)
            try:
                self.del_contact_server(del_contact_name)
            except ServerError:
                LOGGER.error('Failed to send information to server.')
            else:
                print(f'Contact {del_contact_name} successfully deleted.')
                return True
        else:
            LOGGER.info('Attempt to delete a nonexistent contact.')

    @Logging()
    def del_contact_server(self, del_contact_name):
        message = {
            ACTION: DELETE_CONTACT,
            TIME: time.time(),
            USER: self.client_login,
            ACCOUNT_NAME: del_contact_name
        }
        with LOCK_SOCKET:
            send_msg(self.connection, message)
            answer = get_msg(self.connection)
        if RESPONSE in answer and answer[RESPONSE] == 200:
            logging.debug(f'Successfully delete a contact {del_contact_name} at the user {self.client_login}')
        else:
            raise ServerError('Client uninstall error.')

    @Logging()
    def exit_client(self):
        try:
            send_msg(self.connection, self.create_exit_message(self.client_login))
        except ConnectionResetError:
            LOGGER.critical('Lost server connection.')
            exit(1)
        LOGGER.info('Application shutdown by user command\n.')
        print('Application shutdown by user command.')

    @Logging()
    def create_exit_message(self, client_login):
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: client_login
        }


@Logging()
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


@Logging()
def loading_window(app, client_transport):
    loading = LoadingWindow(app)
    loading.init_ui()
    loading.make_connection_with_signals(client_transport)
    app.exec_()


@Logging()
def main():
    app = QApplication(sys.argv)
    ip_server, port_server, client_login, client_password = get_args()
    client_login, client_password = start_dialog(app, client_login, client_password)

    database = ClientDB(client_login)

    encrypt_decrypt = EncryptDecrypt(client_login)

    client_transport = Client(ip_server, port_server, client_login, client_password, database, encrypt_decrypt)
    client_transport.daemon = True
    client_transport.start()

    #  Open loading window
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
