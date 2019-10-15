"""

1. Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться
доступность сетевых узлов. Аргументом функции является список, в котором каждый
сетевой узел должен быть представлен именем хоста или ip-адресом.
В функции необходимо перебирать ip-адреса и проверять их доступность
с выводом соответствующего сообщения («Узел доступен», «Узел недоступен»).
При этом ip-адрес сетевого узла должен создаваться с помощью функции ip_address().

"""

from subprocess import Popen, PIPE
from ipaddress import ip_address
import re


def host_ping(ip_lst):
    result = []
    for ip in ip_lst:
        args = ['ping', str(ip)]
        ping = Popen(args, stdout=PIPE, universal_newlines=True)
        data = ping.communicate()
        # print(data)
        if re.search('unreachable', data[0]):
                result.append((ip, False))
        else:
            result.append((ip, True))
    return result


def main():
    addr = [ip_address('192.168.178.24'), ip_address('192.168.178.14'),
            ip_address('192.168.178.26'), ip_address('192.168.178.25'),
            ip_address('87.240.139.194'), ip_address('179.60.195.174')]

    for ip, result in host_ping(addr):
        if result:
            print(f'Узел {ip} доступен')
        else:
            print(f'Узел {ip} недоступен')


if __name__ == '__main__':
    main()
