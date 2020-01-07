from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, BLOB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()


class ClientDB:
    """Create tables in database. Interacts with the database of this client"""
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
        contact = Column(String)
        direction = Column(String)
        message = Column(Text)
        date = Column(DateTime)

        def __init__(self, contact, direction, message, date):
            self.contact = contact
            self.direction = direction
            self.message = message
            self.date = date

        def __repr__(self):
            return "<User('%s','%s', '%s, '%s')>" % \
                   (self.contact, self.direction, self.message, self.date)

    class Image(Base):
        __tablename__ = 'image'
        id = Column(Integer, primary_key=True)
        path = Column(String)

        def __init__(self, path):
            self.path = path

        def __repr__(self):
            return "<Image(%s)>" % self.path

    def __init__(self, login):
        # echo - logging, 7200 - seconds restart connect
        self.login = login
        self.database_engine = create_engine(f'sqlite:///client_{self.login}.db3',
                                             echo=False, pool_recycle=7200,
                                             connect_args={'check_same_thread': False})
        Base.metadata.create_all(self.database_engine)
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

    def add_contacts(self, contacts_list):
        #  contacts-list - contact list from server
        self.session.query(self.Contacts).delete()
        self.session.commit()
        for contact in contacts_list:
            self.add_contact(contact)

    def add_known_users(self, users_all):
        #  users_all - from server
        self.session.query(self.UsersKnown).delete()
        for user in users_all:
            user_new = self.UsersKnown(user)
            self.session.add(user_new)
        self.session.commit()

    def get_known_users(self):
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

    def is_user(self, login):
        if self.session.query(self.UsersKnown).filter_by(login=login).count():
            return True
        return False

    def is_contact(self, contact):
        if self.session.query(self.Contacts).filter_by(contact=contact).count():
            return True
        else:
            return False

    def save_message(self, contact, direction, message):
        # Message save function
        message_row = self.HistoryMessages(contact, direction, message, datetime.datetime.now())
        self.session.add(message_row)
        self.session.commit()

    def get_history(self, contact):
        # Function returning correspondence history
        query = self.session.query(self.HistoryMessages).filter_by(contact=contact)
        return [(history_row.contact, history_row.direction, history_row.message, history_row.date)
                for history_row in query.all()]

    def add_image(self, path):
        img = self.Image(path)
        self.session.add(img)
        self.session.commit()

    def get_search_contact(self, login):
        """ Search contact in Contacts"""
        contacts = self.session.query(self.Contacts.contact).filter(self.Contacts.contact.ilike(f'%{login}%'))
        return [contact[0] for contact in contacts.all()]

    def get_search_message(self, contact, text):
        """Search message in history"""
        query = self.session.query(self.HistoryMessages).filter(self.HistoryMessages.contact.like(f'{contact}'),
                                                      self.HistoryMessages.message.ilike(f'%{text}%'))
        return [(history_row.contact, history_row.direction, history_row.message, history_row.date)
                for history_row in query.all()]
