DEFAULT_IP_ADDRESS = '127.0.0.1'
DEFAULT_PORT = 7777
MAX_CONNECTIONS = 3
ENCODING = 'utf-8'
MAX_PACKAGE_LENGTH = 1024
# База данных для хранения данных сервера:
SERVER_DATABASE = 'sqlite:///server_base.db3'


# JIM поля
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
RESPONSE = 'response'
ERROR = 'error'
ALERT = 'alert'  # текст сообщения ошибки
ROOM = 'room'  # чат
MESSAGE_TEXT = 'msg_text'
FROM = 'from'
TO = 'to'
EXIT = 'exit'

# значения action
PRESENCE = 'presence'  # при подключении к серверу клиента
PROBE = 'probe'  # доступность пользователя online
QUIT = 'quit'  # выход
AUTHENTICATE = 'authenticate'  # авторизация
MESSAGE = 'msg'
JOIN = 'join'  # присоединиться к чату
LEAVE = 'leave'  # покинуть чать
GET_CONTACTS = 'get_contacts'
LIST_INFO = 'data_list'
DELETE_CONTACT = 'del_contact'
ADD_CONTACT = 'add_contact'
USERS_REQUEST = 'get_users'

# code
BASIC_NOTICE = 100
OK = 200
CREATED = 201  # объект создан
ACCEPTED = 202  # подтверждение
SERVER_ERROR = 500
WRONG_REQUEST = 400  # неправильный запрос

