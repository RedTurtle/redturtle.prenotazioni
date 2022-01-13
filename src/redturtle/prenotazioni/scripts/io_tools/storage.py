# -*- encoding: utf-8 -*-
from . import logger


class Storage(object):
    def get_message(self, key):
        raise NotImplementedError

    def create_message(self, key, fiscal_code, subject, body, payment_data, due_date):
        raise NotImplementedError

    def update_message(self, key, **kwargs):
        raise NotImplementedError


class LogStorage(Storage):
    def __init__(self, logger=logger):
        self.logger = logger

    def get_message(self, key):
        self.logger.info("get_message %s", key)

    def create_message(self, key, fiscal_code, subject, body, payment_data, due_date):
        self.logger.info(
            "create_message %s %s %s %s %s %s",
            key,
            fiscal_code,
            subject,
            body,
            payment_data,
            due_date,
        )

    def update_message(self, key, **kwargs):
        self.logger.info("update_message %s %s", key, kwargs)


logstorage = LogStorage(logger)
