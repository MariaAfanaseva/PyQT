from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from common.variables import *
import datetime

Base = declarative_base()


class ClientDB:
    class UsersKnown(Base):
        __tablename__ = 'users_known'
        id = Column(Integer, primary_key=True)
        login = Column(String, unique=True)

        def __init__(self, login):
            self.login = login

        def __repr__(self):
            return "<User(%s)>" % self.login

    class Contacts(Base):
        __tablename__ = 'contacts'
        id = Column(Integer, primary_key=True)
        contact = Column(String, unique=True)

        def __init__(self, contact):
            self.contact = contact

        def __repr__(self):
            return "<Contact(%s)>" % self.contact

    class HistoryMessages(Base):
        __tablename__ = 'history_messages'
        id = Column(Integer, primary_key=True)
        from_user = Column(String)
        to_user = Column(String)
        message = Column(Text)
        data = Column(DateTime)

        def __init__(self, from_user, to_user, message, data):
            self.from_user = from_user
            self.to_user = to_user
            self.message = message
            self.data = data

        def __repr__(self):
            return "<User('%s','%s', '%s, '%s')>" % \
                   (self.from_user, self.to_user, self.message, self.data)

    def __init__(self, login):
        self.database_engine = create_engine(f'sqlite:///client_{login}.db3', echo=False, pool_recycle=7200,
                      connect_args={'check_same_thread': False})
        Base.metadata.create_all(self.database_engine)
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

    def add_contacts(self, contacts_list):
        #  contacts-list - список контактов из сервера
        self.session.query(self.Contacts).delete()
        self.session.commit()
        for contact in contacts_list:
            self.add_contact(contact)

    def add_users_known(self, users_all):
        #  users_all - Получаем с сервера
        self.session.query(self.UsersKnown).delete()
        for user in users_all:
            user_new = self.UsersKnown(user)
            self.session.add(user_new)
        self.session.commit()

    def get_users_known(self):
        return [user[0] for user in self.session.query(self.UsersKnown.login).all()]

    def add_contact(self, contact):
        if not self.session.query(self.Contacts).filter_by(contact=contact).count():
            contact = self.Contacts(contact)
            self.session.add(contact)
            self.session.commit()

    def del_contact(self, contact):
        self.session.query(self.Contacts).filter_by(contact=contact).delete()

    def get_contacts(self):
        return [user[0] for user in self.session.query(self.Contacts.contact).all()]

    def check_user(self, login):
        if self.session.query(self.UsersKnown).filter_by(login=login).count():
            return True
        return False

    def check_contact(self, contact):
        if self.session.query(self.Contacts).filter_by(name=contact).count():
            return True
        else:
            return False


if __name__ == '__main__':
    client = ClientDB('maria')
    client.get_users_known()
    client.get_contacts()