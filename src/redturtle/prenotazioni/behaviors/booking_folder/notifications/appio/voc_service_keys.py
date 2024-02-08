# -*- coding: utf-8 -*-
import os
from logging import getLogger

import yaml
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

logger = getLogger(__name__)


def load_yaml_config():
    filepath = os.environ.get("APPIO_CONFIG_FILE")
    if not filepath:
        return []
    try:
        with open(filepath, "r") as config:
            return yaml.safe_load(config)

    except FileNotFoundError:
        logger.error(f'Filepath "{filepath}" does not exist.')

    return []


APPIO_CONFIG = load_yaml_config()


@implementer(IVocabularyFactory)
class VocPrenotazioneTypeGatesFactory(object):
    """ """

    def __call__(self, context):
        terms = []

        for item in APPIO_CONFIG:
            terms.append(
                SimpleTerm(
                    value=item["key"],
                    token=item["name"],
                    title=item["name"],
                )
            )

        return SimpleVocabulary(terms)


VocPrenotazioneTypeGatesFactory = VocPrenotazioneTypeGatesFactory()
