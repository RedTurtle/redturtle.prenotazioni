# -*- coding: utf-8 -*-
import base64
import os

import yaml
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


def load_yaml_config():
    return yaml.safe_load(
        base64.b64decode(os.environ.get("APPIO_CONFIG_STREAM", "")).decode("utf-8")
    )


@implementer(IVocabularyFactory)
class VocPrenotazioneTypeGatesFactory(object):
    """ """

    def __call__(self, context):
        terms = []

        for item in load_yaml_config():
            terms.append(
                SimpleTerm(
                    value=item["key"],
                    token=item["name"],
                    title=item["name"],
                )
            )

        return SimpleVocabulary(terms)


VocPrenotazioneTypeGatesFactory = VocPrenotazioneTypeGatesFactory()
