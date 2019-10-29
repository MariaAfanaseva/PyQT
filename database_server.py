from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from common.variables import *
import datetime

Base = declarative_base()


class ServerDB:
    class AllUsers(Base):
        __tablename__ = 'users_all'
        id = Column(Integer, primary_key=True)
        login = Column(String, unique=True)
        fullname = Column(String)
        password_hash = Column(String)
        last_login = Column(DateTime)
        pubkey = Column(Text)

        def __init__(self, login, fullname=None, password_hash=None, pubkey=None):
            self.login = login
            self.fullname = fullname
            self.password_hash = password_hash
            self.last_login = datetime.datetime.now()

        def __repr__(self):
            return "<User('%s, '%s', '%s, '%s')>" % \
                   (self.login, self.fullname, self.password_hash, self.pubkey)

    class ActiveUsers(Base):
        __tablename__ = 'users_active'
        id = Column(Integer, primary_key=True)
        user_id = Column(ForeignKey('users_all.id'), unique=True)
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
        __tablename__ = 'history_login'
        id = Column(Integer, primary_key=True)
        user_id = Column(ForeignKey('users_all.id'))
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

    class ContactsUsers(Base):
        __tablename__ = 'users_contacts'
        id = Column(Integer, primary_key=True)
        user_id = Column(ForeignKey('users_all.id'))
        contact = Column(ForeignKey('users_all.id'))

        def __init__(self, user_id, contact):
            self.user_id = user_id
            self.contact = contact

        def __repr__(self):
            return "<User('%s','%s')>" % \
                   (self.user_id, self.contact)

    class UsersHistory(Base):
        __tablename__ = 'users_history'
        id = Column(Integer, primary_key=True)
        user_id = Column(ForeignKey('users_all.id'))
        send = Column(Integer)
        accepted = Column(Integer)

        def __init__(self, user_id, send=0, accepted=0):
            self.user_id = user_id
            self.send = send
            self.accepted = accepted

        def __repr__(self):
            return "<User('%s','%s,'%s')>" % \
                   (self.user_id, self.send, self.accepted)

    def __init__(self, path):
        # echo=False - disable logging (output sql queries)
        # pool_recycle - By default, the connection to the database is terminated after 8 hours of inactivity.
        # pool_recycle = 7200 - reconnect after 2 hours
        self.database_engine = create_engine(f'sqlite:///{path}', echo=False, pool_recycle=7200,
                                             connect_args={'check_same_thread': False})

        Base.metadata.create_all(self.database_engine)

        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        # When we establish a connection, we clear the table of active users
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def login_user(self, login, ip_address, port, password_hash, key, fullname=None):
        user = self.session.query(self.AllUsers).filter_by(login=login)
        if user.count():
            user = user.first()
            user.last_login = datetime.datetime.now()
            if user.pubkey != key:
                user.pubkey = key
        else:
            raise ValueError('Пользователь не зарегистрирован.')

        now_time = datetime.datetime.now()

        active_user_new = self.ActiveUsers(user.id, ip_address, port, now_time)
        self.session.add(active_user_new)

        new_history = self.HistoryLogin(user.id, now_time, ip_address, port)
        self.session.add(new_history)
        self.session.commit()

    def add_user(self, login, password_hash, fullname=None):
        user = self.AllUsers(login, fullname, password_hash)
        self.session.add(user)
        self.session.commit()

        add_in_history = self.UsersHistory(user.id)
        self.session.add(add_in_history)
        self.session.commit()

    def remove_user(self, login):
        user = self.session.query(self.AllUsers).filter_by(login=login).first()
        self.session.query(self.ActiveUsers).filter_by(user_id=user.id).delete()
        self.session.query(self.HistoryLogin).filter_by(user_id=user.id).delete()
        self.session.query(self.ContactsUsers).filter_by(user_id=user.id).delete()
        self.session.query(self.UsersHistory).filter_by(user_id=user.id).delete()
        self.session.query(self.AllUsers).filter_by(login=login).delete()
        self.session.commit()

    def get_hash(self, login):
        user = self.session.query(self.AllUsers).filter_by(login=login).first()
        return user.password_hash

    def get_pubkey(self, login):
        user = self.session.query(self.AllUsers).filter_by(login=login).first()
        return user.pubkey

    def user_logout(self, login):
        user = self.session.query(self.AllUsers).filter_by(login=login).first()
        self.session.query(self.ActiveUsers).filter_by(user_id=user.id).delete()
        self.session.commit()

    def add_contact(self, user, contact):
        user = self.session.query(self.AllUsers).filter_by(login=user).first()
        contact = self.session.query(self.AllUsers).filter_by(login=contact).first()

        if not contact or self.session.query(self.ContactsUsers).filter_by(user_id=user.id, contact=contact.id).count():
            return

        new_contact = self.ContactsUsers(user_id=user.id, contact=contact.id)
        self.session.add(new_contact)
        self.session.commit()

    def delete_contact(self, user, contact):
        user = self.session.query(self.AllUsers).filter_by(login=user).first()
        contact = self.session.query(self.AllUsers).filter_by(login=contact).first()

        if not contact:
            return

        self.session.query(self.ContactsUsers).filter_by(user_id=user.id,
                                                         contact=contact.id).delete()
        self.session.commit()

    def sending_message(self, sender, receiver):
        sender_id = self.session.query(self.AllUsers).filter_by(login=sender).first().id
        receiver_id = self.session.query(self.AllUsers).filter_by(login=receiver).first().id
        sender_send = self.session.query(self.UsersHistory).filter_by(user_id=sender_id).first()
        sender_send.send += 1
        receiver_acc = self.session.query(self.UsersHistory).filter_by(user_id=receiver_id).first()
        receiver_acc.accepted += 1
        self.session.commit()

    def get_contacts(self, login_user):
        user = self.session.query(self.AllUsers).filter_by(login=login_user).one()
        contacts = self.session.query(self.ContactsUsers, self.AllUsers.login).\
            filter_by(user_id=user.id).\
            join(self.AllUsers, self.ContactsUsers.contact == self.AllUsers.id)
        contacts = [contact[1] for contact in contacts.all()]
        return contacts

    def users_active_list(self):
        users = self.session.query(
            self.AllUsers.login,
            self.ActiveUsers.ip_addr,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time
        ).join(self.AllUsers)
        return users.all()

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

    def users_all(self):
        users = self.session.query(
            self.AllUsers.login,
            self.AllUsers.fullname,
            self.AllUsers.last_login
        )
        return users.all()

    def history_message(self):
        history = self.session.query(self.AllUsers.login,
                                     self.AllUsers.last_login,
                                     self.UsersHistory.send,
                                     self.UsersHistory.accepted).join(self.AllUsers)
        return history.all()


if __name__ == '__main__':
    server = ServerDB()
    # server.add_user()
    server.login_user('maria4', '127.0.0.1', 7777)
    server.login_user('maria5', '127.0.0.1', 7777)
    server.login_user('maria6', '127.0.0.1', 7777)
    # print(server.users_active_list())
    # server.user_logout('maria2')
    # print(server.history_login('maria2'))
    # print(server.users_all())
    # server.add_contact('maria2', 'maria1')
    # server.add_contact('maria2', 'maria')
    # server.delete_contact('maria2', 'maria1')
    # print(server.get_contacts('maria2'))
    # server.sending_message('maria5', 'maria3')

