# # -*- coding: utf-8 -*-
# # Extends for PrenotazioniFolderSchema
# from Products.Archetypes.atapi import (
#     AnnotationStorage,
#     LinesField,
#     MultiSelectionWidget,
#     StringField,
#     StringWidget,
# )
# from archetypes.schemaextender.field import ExtensionField
# from pd.prenotazioni import prenotazioniMessageFactory as _


# class ExtensionStringField(ExtensionField, StringField):
#     """derivative of StringField for extending schemas
#     """


# class ExtensionLinesField(ExtensionField, LinesField):
#     """derivative of LinesField for extending schemas
#     """


# class PrenotazioniFolderSchemaExtender(object):

#     """ extender for prenotazioni
#     """

#     fields = [
#         ExtensionLinesField(
#             'required_booking_fields',
#             storage=AnnotationStorage(),
#             widget=MultiSelectionWidget(
#                 label=_(
#                     'label_required_booking_fields',
#                     u"Required booking fields"
#                 ),
#                 description=_(
#                     'help_required_booking_fields',
#                     u'User will not be able to add a booking unless those '
#                     u'fields are filled. '
#                     u'Remember that, '
#                     u'whatever you selected in this list, '
#                     u'users have to supply at least one '
#                     u'of "Email", "Mobile", or "Telephone"'
#                 ),
#                 helper_js=(),
#                 helper_css=(),
#                 format='checkbox',
#             ),
#             default=(),
#             required=False,
#             vocabulary_factory='pd.prenotazioni.requirable_booking_fields',
#             enforceVocabulary=True,
#         ),
#         ExtensionStringField(
#             'same_day_booking_disallowed',
#             storage=AnnotationStorage(),
#             widget=StringWidget(
#                 label=_(
#                     'label_same_day_booking_disallowed',
#                     u"Same day booking disallowed"
#                 ),
#                 description=_(
#                     'help_same_day_booking_disallowed',
#                     u"States if it is not allowed to reserve a booking "
#                     u"during the current day"
#                 ),
#                 macro="same_day_booking_disallowed",
#                 helper_js=(),
#                 helper_css=(),
#             ),
#             default='',
#             required=True,
#         ),
#     ]

#     def __init__(self, context):
#         self.context = context

#     def getFields(self):
#         return self.fields

#     def fiddle(self, schema):
#         schema.moveField(
#             'required_booking_fields',
#             after='descriptionAgenda'
#         )
#         schema.moveField(
#             'same_day_booking_disallowed',
#             after='aData'
#         )
