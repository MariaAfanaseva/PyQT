from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from common.variables import *
import datetime

Base = declarative_base()


class ServerDB:
    # Класс - отображение таблицы всех пользователей
    class AllUsers(Base):
        __tablename__ = 'AllUsers'
        id = Column(Integer, primary_key=True)
        login = Column(String, unique=True)
        fullname = Column(String)
        password = Column(String)
        last_login = Column(DateTime)

        def __init__(self, login, fullname=None, password=None):
            self.login = login
            self.fullname = fullname
            self.password = password
            self.last_login = datetime.datetime.now()

        def __repr__(self):
            return "<User('%s, '%s', '%s')>" % \
                   (self.login, self.fullname, self.password)

        # Класс - отображение таблицы активных пользователей
    class ActiveUsers(Base):
        __tablename__ = 'ActiveUsers'
        id = Column(Integer, primary_key=True)
        user_id = Column(ForeignKey('AllUsers.id'), unique=True)
        ip_addr = Column(String)
        port = Column(Integer)
        login_time = Column(DateTime)

        def __init__(self, user_id, ip_addr, port, login_time):
            self.user_id = user_id
            self.ip_addr = ip_addr
            self.port = port
            self.login_time = login_time

        def __repr__(self):
            return "<User('%s','%s', '%s, '%s')>" % \
                   (self.user_id, self.ip_addr, self.port, self.login_time)

    class HistoryLogin(Base):
        __tablename__ = 'HistoryLogin'
        id = Column(Integer, primary_key=True)
        user_id = Column(ForeignKey('AllUsers.id'))
        login_time = Column(DateTime)
        ip_addr = Column(String)
        port = Column(Integer)

        def __init__(self, user_id, login_time, ip_addr, port):
            self.user_id = user_id
            self.login_time = login_time
            self.ip_addr = ip_addr
            self.port = port

        def __repr__(self):
            return "<User('%s','%s', '%s, '%s')>" % \
                   (self.user_id, self.login_time, self.ip_addr, self.port)

    def __init__(self):
        # Создаём движок базы данных
        # SERVER_DATABASE - sqlite:///server_base.db3
        # echo=False - отключение ведение лога (вывод sql-запросов)
        # pool_recycle - По умолчанию соединение с БД через 8 часов простоя обрывается.
        # Чтобы это не случилось нужно добавить опцию pool_recycle = 7200 (переуст-ка соед-я через 2 часа)
        self.database_engine = create_engine(SERVER_DATABASE, echo=False, pool_recycle=7200)
        #  Создание всех таблиц
        Base.metadata.create_all(self.database_engine)
        #  Создание сессии
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        # Если в таблице активных пользователей есть записи, то их необходимо удалить
        # Когда устанавливаем соединение, очищаем таблицу активных пользователей
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def add_user(self):
        user = self.AllUsers("maria2", "Pypkin", "vasia2000")
        self.session.add(user)
        q_user = self.session.query(self.AllUsers).filter_by(login="maria2").first()
        print('Simple query:', q_user)
        self.session.commit()
        print(user.id)

    # Функция выполняющяяся при входе пользователя, записывает в базу ActiveUsers
    def login_user(self, login, ip_address, port, fullname=None, password=None):
        # Запрос в таблицу пользователей на наличие там пользователя с таким именем
        user = self.session.query(self.AllUsers).filter_by(login=login)
        # print(user)
        if user.count():
            user = user.first()
            user.last_login = datetime.datetime.now()
        # Если нет, то создаздаём нового пользователя
        else:
            # Создаем экземпляр класса self.AllUsers, через который передаем данные в таблицу
            user = self.AllUsers(login, fullname, password)
            self.session.add(user)
            self.session.commit()
            # Комит здесь нужен, чтобы присвоился id и разблокировалась таблица
        now_time = datetime.datetime.now()
        #  Создаем запись в таблицу ActiveUsers
        active_user_new = self.ActiveUsers(user.id, ip_address, port, now_time)
        self.session.add(active_user_new)

        #  Сохраняем в историю входов
        new_history = self.HistoryLogin(user.id, now_time, ip_address, port)
        self.session.add(new_history)
        self.session.commit()

    # Функция фиксирующая отключение пользователя
    def user_logout(self, login):
        user = self.session.query(self.AllUsers).filter_by(login=login).first()
        self.session.query(self.ActiveUsers).filter_by(user_id=user.id).delete()
        self.session.commit()

    # Функция возвращает список активных пользователей
    def users_active_list(self):
        # Запрашиваем соединение таблиц и собираем кортежи имя, адрес, порт, время
        users = self.session.query(
            self.AllUsers.login,
            self.ActiveUsers.ip_addr,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time
        ).join(self.AllUsers)
        return users.all()

    # Функция возвращающая историю входов по пользователю или всем пользователям
    def history_login(self, login=None):
        history = self.session.query(
            self.AllUsers.login,
            self.HistoryLogin.ip_addr,
            self.HistoryLogin.port,
            self.HistoryLogin.login_time
        ).join(self.AllUsers)
        if login:
            history = history.filter_by(login=login)
        return history.all()

    # Функция возвращает список известных пользователей со временем последнего входа.
    def users_all(self):
        users = self.session.query(
            self.AllUsers.login,
            self.AllUsers.fullname,
            self.AllUsers.last_login
        )
        return users.all()


if __name__ == '__main__':
    server = ServerDB()
    # server.add_user()
    server.login_user('maria2', '127.0.0.1', 7777)
    server.login_user('maria1', '127.0.0.1', 7777)
    server.login_user('maria', '127.0.0.1', 7777)
    # print(server.users_active_list())
    # server.user_logout('maria2')
    print(server.history_login('maria2'))
    print(server.users_all())

