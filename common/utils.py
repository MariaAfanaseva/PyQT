import json
from common.variables import *
from common.errors import IncorrectDataNotDictError
from decorators.decos import DecorationLogging


@DecorationLogging()
def send_msg(socket, msg):
    json_msg = json.dumps(msg)
    coding_msg = json_msg.encode(ENCODING)
    socket.send(coding_msg)


def get_msg(client):
    json_response = client.recv(MAX_PACKAGE_LENGTH).decode(ENCODING)
    response = json.loads(json_response)
    if isinstance(response, dict):
        return response
    else:
        raise IncorrectDataNotDictError
