"""

3. Написать функцию host_range_ping_tab(), возможности которой основаны на функции из
примера 2. Но в данном случае результат должен быть итоговым по всем ip-адресам,
представленным в табличном формате (использовать модуль tabulate).
Таблица должна состоять из двух колонок и выглядеть примерно так:

"""

from tabulate import tabulate
from ping_range import host_range_ping


def print_result(lst_result):
    header = ['Address', 'Reachable']
    print(tabulate(lst_result, headers=header, tablefmt='grid'))


def main():
    print_result(host_range_ping())


if __name__ == '__main__':
    main()
