import dis


# Метакласс для проверки соответствия сервера:
class ServerCreator(type):
    def __init__(self, name_class, bases_classes, dict_class):
        # name_class - экземпляр метакласса - Server
        # bases_classes - кортеж базовых классов - ()
        # dict_class - словарь атрибутов и методов экземпляра метакласса
        methods_class = []
        attrs_class = []
        # print(dict_class)
        for func in dict_class:
            try:
                instr = dis.get_instructions(dict_class[func])
            except TypeError:
                pass
            else:
                 for i in instr:
                    # print(i)
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods_class:
                            methods_class.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs_class:
                           attrs_class.append(i.argval)
        # print(attrs_class)
        # print(methods_class)
        if 'connect' in methods_class:
            raise TypeError('Использование метода connect недопустимо в серверном классе')
        if not ('SOCK_STREAM' in attrs_class and 'AF_INET' in attrs_class):
            raise TypeError('Некорректная инициализация сокета.')
        super().__init__(name_class, bases_classes, dict_class)


class ClientCreator(type):
    def __init__(self, name_class, bases_classes, dict_class):
        methods = []
        attrs = []
        for func in dict_class:
            try:
                instr = dis.get_instructions(dict_class[func])
            except TypeError:
                pass
            else:
                for i in instr:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs:
                            attrs.append(i.argval)
        if not ('SOCK_STREAM' in attrs and 'AF_INET' in attrs):
            raise TypeError('Некорректная инициализация сокета.')
        for command in ('accept', 'listen'):
            if command in methods:
                print(methods)
                raise TypeError(f'В классе обнаружено использование запрещённого метода {command}')
        if 'get_msg' in methods or 'send_msg' in methods:
            pass
        else:
            raise TypeError('Отсутствуют вызовы функций, работающих с сокетами.')
        super().__init__(name_class, bases_classes, dict_class)
