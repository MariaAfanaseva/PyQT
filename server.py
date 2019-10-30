import socket
import sys
import logging
import argparse
import select
import time
import threading
import configparser
import os
import binascii
import hmac
from common.utils import *
from common.errors import IncorrectDataNotDictError
from decorators.decos import DecorationLogging
from descriptors import CheckPort, CheckIP
from metaclasses import ServerCreator
from database_server import ServerDB
from PyQt5.QtWidgets import QApplication
from server.gui_main_window import MainWindow

logger = logging.getLogger('server')
logger.setLevel(logging.DEBUG)


# Get arguments when starting the file.
@DecorationLogging()
def get_args(default_ip, default_port):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default=default_port, type=int)
    parser.add_argument('-a', '--addr', default=default_ip)
    names = parser.parse_args(sys.argv[1:])
    address = names.addr
    port = names.port
    return address, port


def read_config_file():
    # Download server configuration file
    parser = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(dir_path, f'server\\{CONFIG_FILE_NAME}')
    parser.read(file_path, encoding='utf-8')
    port = parser['SETTINGS']['default_port']
    ip_addr = parser['SETTINGS']['listen_Address']
    db_path = parser['SETTINGS']['database_path']
    return ip_addr, port, db_path


class Server(threading.Thread, metaclass=ServerCreator):
    # Port and Address Correction Descriptors
    listen_port = CheckPort()
    listen_ip = CheckIP()

    def __init__(self, listen_ip, listen_port, database):
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.database = database

        self.clients = []   # All clients

        self.messages = []  # All messages

        self.names = dict()  # Connected Client Names
        super().__init__()

    def socket_init(self):
        # Create a socket
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Готовим сокет
        connection.bind((self.listen_ip, self.listen_port))
        connection.settimeout(0.5)
        connection.listen(MAX_CONNECTIONS)  # Слушаем порт

        self.connection = connection

    @DecorationLogging()
    def print_help(self):
        print('Supported Commands: \n'
              'users - list of known users \n'
              'connected - list of connected users \n'
              'history - user login history \n'
              'exit - server shutdown. \n'
              'help - display help for supported commands')

    @DecorationLogging()
    def get_information(self):
        time.sleep(1)
        self.print_help()
        while True:
            command = input('Enter command: ')
            if command == 'help':
                self.print_help()
            elif command == 'exit':
                break
            elif command == 'users':
                for user in sorted(self.database.users_all()):
                    print(f'User with login {user [0]}, last login: {user[2]}')
            elif command == 'connected':
                for user in sorted(self.database.users_active_list()):
                    print(f'The user with the login {user [0]} is connected ip - {user[1]} port - {user[2]}, '
                          f'connection setup time: {user[3]}')
            elif command == 'history':
                login = input(
                    'Enter user login to view history. To display the whole story, just press Enter: ')
                for user in sorted(self.database.history_login(login)):
                    print(f'User: {user [0]} login time: {user [3]}. Login from: ip - {user[1]} port - {user[2]}')
            else:
                print('Wrong command.')

    @DecorationLogging()
    def run(self):
        # Information output on the server in a separate stream
        server_info = threading.Thread(target=self.get_information)
        server_info.daemon = True
        server_info.start()

        self.socket_init()
        # The main loop of the server program
        # We are waiting for a connection, if the timeout has expired, we catch an exception.
        while True:
            try:
                client, client_address = self.connection.accept()
            except OSError:
                pass
            else:
                logger.info(f'Connection to client established - {client_address}.')
                self.clients.append(client)

            clients_read_lst = []
            clients_send_lst = []
            err_lst = []

            try:
                if self.clients:
                    clients_read_lst, clients_send_lst, err_lst = select.select(self.clients, self.clients, [], 0)
            except OSError as err:
                logger.error(f'Error working with sockets: {err}')

            # Receive a message from clients
            if clients_read_lst:
                for client in clients_read_lst:
                    try:
                        message = get_msg(client)
                    except IncorrectDataNotDictError:
                        logger.error('Invalid data format received.')
                    except (ConnectionResetError, json.decoder.JSONDecodeError, ConnectionAbortedError):
                        self.remove_client(client)
                    else:
                        logger.debug(f'Received message from client {message}.')
                        self.client_msg(message, client)

            # If there are messages to send and pending clients, send them a message.
            if self.messages:
                for msg in self.messages:
                    try:
                        self.send_messages_users(clients_send_lst, msg)
                    except (ConnectionResetError, ConnectionError):
                        logger.info(f'Communication with a client named {msg [TO]} has been lost.')
                        self.clients.remove(self.names[msg[TO]])
                        del self.names[msg[TO]]
                        self.database.user_logout(msg[TO])
                self.messages.clear()
                
    @DecorationLogging()
    def client_authorization(self, client, message):
        if message[USER][ACCOUNT_NAME] in self.names.keys():
            response = RESPONSE_400
            response[ERROR] = 'Login already taken.'
            try:
                send_msg(client, response)
            except OSError:
                pass
            self.clients.remove(client)
            client.close()
            logger.debug(f'Username is already taken. Response sent to client - {response} \n')
        elif not self.database.is_user(message[USER][ACCOUNT_NAME]):
            response = RESPONSE_400
            response[ERROR] = 'User not registered.'
            try:
                send_msg(client, response)
            except OSError:
                pass
            self.clients.remove(client)
            client.close()
            logger.debug(f'The user is not registered. Response sent to client - {response} \n')
        else:
            message_auth = RESPONSE_511
            random_str = binascii.hexlify(os.urandom(64))
            # Bytes cannot be in the dictionary, decode (json.dumps -> TypeError)
            message_auth[DATA] = random_str.decode('ascii')
            password_hash = self.database.get_hash(message[USER][ACCOUNT_NAME])
            hash = hmac.new(password_hash, random_str)
            server_digest = hash.digest()
            
            try:
                send_msg(client, message_auth)
                answer = get_msg(client)
            except OSError:
                client.close()
                return
            
            client_digest = binascii.a2b_base64(answer[DATA])
            
            # If the client’s answer is correct, then save it to the list of users.
            if RESPONSE in answer and answer[RESPONSE] == 511 and hmac.compare_digest(server_digest, client_digest):
                self.names[message[USER][ACCOUNT_NAME]] = client
                client_ip, client_port = client.getpeername()
                try:
                    send_msg(client, RESPONSE_200)
                except OSError:
                    self.remove_client(message[USER][ACCOUNT_NAME])

                self.database.login_user(message[USER][ACCOUNT_NAME],
                                         client_ip, client_port, message[USER][PUBLIC_KEY])
            else:
                response = RESPONSE_400
                response[ERROR] = 'Wrong password.'
                try:
                    send_msg(client, response)
                except OSError:
                    pass
                self.clients.remove(client)
                client.close()

    @DecorationLogging()       
    def remove_client(self, client):
        logger.info(f'Client {client.getpeername ()} disconnected from server.')
        for name in self.names:
            if self.names[name] == client:
                self.database.user_logout(name)
                del self.names[name]
                break
        self.clients.remove(client)
        client.close()
        
    @DecorationLogging()
    def client_msg(self, message, client):
        logger.debug(f'Parsing a message from a client - {message}')

        if ACTION in message and TIME in message and USER in message \
                and ACCOUNT_NAME in message[USER] and message[ACTION] == PRESENCE:
            self.client_authorization(client, message)

        elif ACTION in message and message[ACTION] == MESSAGE and\
                TIME in message and MESSAGE_TEXT in message and TO in message and FROM in message:
            if message[TO] in self.names:
                self.messages.append(message)
                send_msg(client, {RESPONSE: 200})
            else:
                send_msg(client, {RESPONSE: 400, ERROR: 'The user is not registered on the server.'})

        elif ACTION in message and message[ACTION] == GET_CONTACTS and USER in message \
                and self.names[message[USER]] == client:
            answer = {
                RESPONSE: 202,
                LIST_INFO: self.database.get_contacts(message[USER])
                }
            send_msg(client, answer)
            logger.debug(f'Contact list sent to {answer [LIST_INFO]} to user - {message[USER]}\n')

        elif ACTION in message and message[ACTION] == ADD_CONTACT \
                and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.add_contact(message[USER], message[ACCOUNT_NAME])
            send_msg(client, {RESPONSE: 200})
            logger.debug(f'New contact added {message[ACCOUNT_NAME]} ay the user {message[USER]}.')

        elif ACTION in message and message[ACTION] == DELETE_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.delete_contact(message[USER], message[ACCOUNT_NAME])
            send_msg(client, {RESPONSE: 200})
            logger.debug(f'Deleted contact {message [ACCOUNT_NAME]} at the user {message [USER]}')

        elif ACTION in message and message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            answer = {
                RESPONSE: 202,
                LIST_INFO: [user[0] for user in self.database.users_all()]
            }
            send_msg(client, answer)

        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            logger.info(f'User {message [ACCOUNT_NAME]} has disconnected.')
            user_name = message[ACCOUNT_NAME]
            self.database.user_logout(user_name)
            self.clients.remove(self.names[user_name])
            self.names[user_name].close()
            del self.names[user_name]

        else:
            msg = {
                RESPONSE: 400,
                ERROR: 'Bad Request'
            }
            send_msg(client, msg)
            logger.info(f'Errors sent to client - {msg}.\n')

    #  We respond to users
    @DecorationLogging()
    def send_messages_users(self, clients_send_lst, msg):
        if msg[TO] in self.names and self.names[msg[TO]] in clients_send_lst:
            send_msg(self.names[msg[TO]], msg)
            self.database.sending_message(msg[FROM], msg[TO])
            logger.info(f'A message was sent to user {msg [TO]} from user {msg [FROM]}.')
        elif msg[TO] in self.names and self.names[msg[TO]] not in clients_send_lst:
            raise ConnectionError
        else:
            logger.error(
                f'User {msg [TO]} is not registered on the server, sending messages is not possible.')


@DecorationLogging()
def main():
    default_ip, default_port, db_path = read_config_file()
    listen_ip, listen_port = get_args(default_ip, default_port)

    database = ServerDB(db_path)
    server = Server(listen_ip, listen_port, database)
    server.daemon = True
    server.start()

    # GUI PyQt5
    app = QApplication(sys.argv)
    main_window = MainWindow(app, database)
    main_window.init_ui()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
