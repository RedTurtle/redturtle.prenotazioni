# -*- encoding: utf-8 -*-
from datetime import datetime

from io_tools.storage import Storage as Base
from pony import orm

db = orm.Database()


class Message_io(db.Entity):
    msgid = orm.Optional(str, nullable=True)
    key = orm.Required(str, unique=True)
    fiscal_code = orm.Required(str)
    subject = orm.Required(str)
    body = orm.Required(str)
    amount = orm.Optional(int, nullable=True)
    notice_number = orm.Optional(str, nullable=True)
    invalid_after_due_date = orm.Optional(bool, nullable=True)
    due_date = orm.Optional(datetime, nullable=True)
    status = orm.Required(str)
    info = orm.Optional(str, nullable=True)

    def __repr__(self):
        return '<{} : {} "{}" {}>'.format(
            self.__class__.__name__,
            self.fiscal_code,
            self.subject,
            self.status,
        )


class Storage(Base):
    def __init__(self, config):
        create_tables = config.pop("create_tables", False)
        db.bind(**config)
        db.generate_mapping(create_tables=create_tables)

    @staticmethod
    @orm.db_session
    def get_data(query, params=None):
        """
        ritorna i dati per costruire i messaggi con una query sul db
        """
        return db.select(query, params)

    @staticmethod
    @orm.db_session
    def get_message(key):
        """Data una chiave di un messaggio ritorna il messaggio salvato nello storage
           o None.

        Args:
            key (string): chiave univoca per un messaggio, va costruita in base a dati del messaggio,
                          non è il msgid registrato su IO. Serve per evitare di inviare due volte lo stesso
                          messaggio

        Returns:
            [Message_io|None]: ritorna un oggetto messaggi con gli attributi definiti nella implementazione di riferimento
                            in io_tools.rdbms.Message_io
        """
        return orm.select(m for m in Message_io if m.key == key).first()

    @staticmethod
    @orm.db_session
    def update_message(key, **kwargs):
        msg = orm.select(m for m in Message_io if m.key == key).first()
        for k, v in kwargs.items():
            setattr(msg, k, v)
        return msg

    @staticmethod
    @orm.db_session
    def create_message(key, fiscal_code, subject, body, payment_data, due_date):
        msg = Message_io(
            key=key,
            fiscal_code=fiscal_code,
            subject=subject,
            body=body,
            amount=payment_data["amount"] if payment_data else None,
            notice_number=payment_data["notice_number"] if payment_data else None,
            invalid_after_due_date=payment_data["invalid_after_due_date"]
            if payment_data
            else None,
            due_date=due_date,
            status="created",
        )
        return msg
