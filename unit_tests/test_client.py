import sys
import os
import unittest
sys.path.append(os.path.join(os.getcwd(), '..'))
from client import get_ip_port, create_presence_msg, valid_server_answer
from common.variables import *
from common.errors import IncorrectDataNotDictError, FieldMissingError, IncorrectCodeError


class TestClient(unittest.TestCase):
    def setUp(self):
        sys.argv = sys.argv[:1]

    def test_get_ip_port(self):
        # print('1', sys.argv)
        self.assertEqual(get_ip_port(), ('127.0.0.1', 7777))

    def test_get_args(self):
        sys.argv.append('44.23.4.4')
        sys.argv.append('5667')
        # print('2', sys.argv)
        self.assertEqual(get_ip_port(), ('44.23.4.4', 5667))

    def test_get_wrong_port(self):
        sys.argv.append('44.23.4.4')
        sys.argv.append('567')
        # print('3', sys.argv)
        self.assertRaises(SystemExit, get_ip_port)

    def test_get_wrong_ip(self):
        sys.argv.append('4444.23.4.4')
        sys.argv.append('5678')
        # print('4', sys.argv)
        self.assertRaises(SystemExit, get_ip_port)

    def test_create_presence_msg_correct(self):
        message = create_presence_msg()
        message[TIME] = 1.1
        self.assertEqual(message, {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'Guest'}})

    def test_create_presence_msg_correct_name(self):
        message = create_presence_msg('Maria')
        message[TIME] = 1.1
        self.assertEqual(message, {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'Maria'}})

    def test_create_presence_msg_wrong(self):
        self.assertRaises(SystemExit, create_presence_msg, 'very very very long username')

    def test_create_presence_msg_wrong_name(self):
        self.assertRaises(SystemExit, create_presence_msg, 789)

    def test_valid_server_answer_200(self):
        self.assertEqual(valid_server_answer({RESPONSE: 200}), 'OK: 200')

    def test_valid_server_answer_400(self):
        self.assertEqual(valid_server_answer({RESPONSE: 400, ERROR: 'Bad Request'}), 'Bad Request: 400')

    def test_valid_server_answer_wrong(self):
        self.assertRaises(IncorrectCodeError, valid_server_answer, {RESPONSE: 700})

    def test_valid_server_answer_wrong_1(self):
        self.assertRaises(FieldMissingError, valid_server_answer, {ERROR: 1.1})


if __name__ == '__main__':
    unittest.main()
