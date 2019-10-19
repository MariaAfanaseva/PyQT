import dis


# Метакласс для проверки соответствия сервера:
class ServerCreator(type):
    def __init__(self, name_class, bases_classes, dict_class):
        # name_class - экземпляр метакласса - Server
        # bases_classes - кортеж базовых классов - ()
        # dict_class - словарь атрибутов и методов экземпляра метакласса

        # Список методов, которые используются в функциях класса:
        methods_class = []
        # Атрибуты, используемые в функциях классов
        attrs_class = []
        # перебираем ключи
        # print(dict_class)
        for func in dict_class:
            try:
                # Возвращает итератор по инструкциям в предоставленной функции
                # , методе, строке исходного кода или объекте кода.
                # Недобираеться до задекорированных функций!
                instr = dis.get_instructions(dict_class[func])
                # Если не функция то ловим исключение
            except TypeError:
                pass
            else:
                # Раз функция разбираем код, получая используемые методы и атрибуты.
                for i in instr:
                    # print(i)
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods_class:
                            # заполняем список методами, использующимися в функциях класса
                            methods_class.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs_class:
                            # заполняем список атрибутами, использующимися в функциях класса
                            attrs_class.append(i.argval)
        # print(attrs_class)
        # print(methods_class)
        # Если обнаружено использование недопустимого метода connect, бросаем исключение:
        if 'connect' in methods_class:
            raise TypeError('Использование метода connect недопустимо в серверном классе')
        # Если сокет не инициализировался константами SOCK_STREAM(TCP) AF_INET(IPv4), тоже исключение.
        if not ('SOCK_STREAM' in attrs_class and 'AF_INET' in attrs_class):
            raise TypeError('Некорректная инициализация сокета.')
        # Обязательно вызываем конструктор предка:
        super().__init__(name_class, bases_classes, dict_class)


# Метакласс для проверки корректности клиентов:
class ClientCreator(type):
    def __init__(self, name_class, bases_classes, dict_class):
        # Список методов, которые используются в функциях класса:
        methods = []
        attrs = []
        for func in dict_class:
            try:
                instr = dis.get_instructions(dict_class[func])
                # Если не функция то ловим исключение
            except TypeError:
                pass
            else:
                # Раз функция разбираем код, получая используемые методы.
                for i in instr:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs:
                            # заполняем список атрибутами, использующимися в функциях класса
                            attrs.append(i.argval)
        # Если обнаружено использование недопустимого метода accept, listen, socket бросаем исключение:
        if not ('SOCK_STREAM' in attrs and 'AF_INET' in attrs):
            raise TypeError('Некорректная инициализация сокета.')
        for command in ('accept', 'listen'):
            if command in methods:
                print(methods)
                raise TypeError(f'В классе обнаружено использование запрещённого метода {command}')
        # Вызов get_message или send_message из utils считаем корректным использованием сокетов
        if 'get_msg' in methods or 'send_msg' in methods:
            pass
        else:
            raise TypeError('Отсутствуют вызовы функций, работающих с сокетами.')
        super().__init__(name_class, bases_classes, dict_class)
