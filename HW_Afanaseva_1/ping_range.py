"""

2. Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона.
Меняться должен только последний октет каждого адреса. По результатам проверки должно
выводиться соответствующее сообщение.


"""

from ping import host_ping
from ipaddress import ip_address
import re


def host_range_ping():
    while True:
        ip_str = input('Введите адрес: ')
        if check_ip(ip_str):
            last = int(ip_str.split('.')[3])
            max_range = 255 - last
            try:
                range_num = int(input(f'Введите диапазон не более {max_range}: '))
            except ValueError:
                print('Вы ввели не число')
                continue
            if range_num <= max_range:
                break
            else:
                print('Вы ввели неверный диапазон')
        else:
            print('Неверный ip\n')

    ipv4 = ip_address(ip_str)
    addr = [ipv4 + i for i in range(1, range_num+1)]
    print(addr)
    return host_ping(addr)


def check_ip(ip):
    if re.match(r'^(([1-9]?[0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.)'
             r'{3}([1-9]?[0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$', ip):
        return True
    else:
        return False


def main():
    for ip, result in host_range_ping():
        if result:
            print(f'Узел {ip} доступен')
        else:
            print(f'Узел {ip} недоступен')


if __name__ == '__main__':
    main()
