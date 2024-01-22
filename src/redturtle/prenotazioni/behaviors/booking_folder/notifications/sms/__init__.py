# -*- coding: utf-8 -*-
from plone import api
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import implementer
from zope.interface import provider
from zope.schema.interfaces import IContextAwareDefaultFactory

from redturtle.prenotazioni import _


@provider(IContextAwareDefaultFactory)
def notify_on_submit_sms_message_default_factory(context):
    return api.portal.translate(
        _(
            "notify_on_submit_sms_message_default_value",
            "[${prenotazioni_folder_title}]: Booking ${booking_type} for ${booking_date} at ${booking_time} has been created.\nSee details or delete it: ${booking_print_url}.",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_confirm_sms_message_default_factory(context):
    return api.portal.translate(
        _(
            "notify_on_confirm_sms_message_default_value",
            "[${prenotazioni_folder_title}]: Booking of ${booking_date} at ${booking_time} has been accepted.\nSee details or delete it: ${booking_print_url}.",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_move_sms_message_default_factory(context):
    return api.portal.translate(
        _(
            "notify_on_move_sms_message_default_value",
            "[${prenotazioni_folder_title}]: The booking scheduling for ${booking_type} was modified.\nThe new one is on ${booking_date} at ${booking_time}.\nSee details or delete it: ${booking_print_url}.",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_refuse_sms_message_default_factory(context):
    return api.portal.translate(
        _(
            "notify_on_refuse_sms_message_default_value",
            "[${prenotazioni_folder_title}]: The booking ${booking_type} of ${booking_date} at ${booking_time} was refused.",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_as_reminder_sms_message_default_factory(context):
    return api.portal.translate(
        _(
            "notify_as_reminder_sms_message_default_value",
            "[${prenotazioni_folder_title}]: This is an automatic reminder about your booking on ${date} for ${booking_type}."
            "\nSee details or delete it: ${booking_print_url}.",
        )
    )


@provider(IFormFieldProvider)
class INotificationSMS(model.Schema):
    notifications_sms_enabled = schema.Bool(
        title=_("notifications_sms_enabled_label", default="SMS notifications"),
        description=_(
            "notifications_sms_enabled_help",
            default="Enable SMS notifications.",
        ),
        default=False,
        required=False,
    )
    notify_on_submit_sms_message = schema.Text(
        title=_(
            "notify_on_submit_message",
            default="[Created] message",
        ),
        description=_(
            "notify_on_submit_message_help",
            default="The message text when a booking has been created.",
        ),
        defaultFactory=notify_on_submit_sms_message_default_factory,
        required=False,
    )
    notify_on_confirm_sms_message = schema.Text(
        title=_(
            "notify_on_confirm_message",
            default="[Confirmed] message",
        ),
        description=_(
            "notify_on_confirm_message_help",
            default="The message text when a booking has been confirmed.",
        ),
        defaultFactory=notify_on_confirm_sms_message_default_factory,
        required=False,
    )
    notify_on_move_sms_message = schema.Text(
        title=_(
            "notify_on_move_message",
            default="[Move] message",
        ),
        description=_(
            "notify_on_move_message_help",
            default="The message text when a booking has been moved.",
        ),
        defaultFactory=notify_on_move_sms_message_default_factory,
        required=False,
    )
    notify_on_refuse_sms_message = schema.Text(
        title=_(
            "notify_on_refuse_message",
            default="[Refuse] message",
        ),
        description=_(
            "notify_on_refuse_message_help",
            default="The message text when a booking has been refused.",
        ),
        defaultFactory=notify_on_refuse_sms_message_default_factory,
        required=False,
    )
    notify_as_reminder_sms_message = schema.Text(
        title=_(
            "notify_as_reminder_message",
            default="[Reminder] message",
        ),
        description=_(
            "notify_as_reminder_message_help",
            default="The message text when a reminder will be sent.",
        ),
        defaultFactory=notify_as_reminder_sms_message_default_factory,
        required=False,
    )

    model.fieldset(
        "sms_notifications",
        label=_(
            "bookings_sms_templates_label",
            default="SMS Notifications",
        ),
        description=_(
            "bookings_sms_templates_help",
            default="Set message text for all available notification events. Remember that SMS has a 160 characters limit. Depending on your gateway service, it can split messages, if you exceed that limit.",
        ),
        fields=[
            "notifications_sms_enabled",
            "notify_on_submit_sms_message",
            "notify_on_confirm_sms_message",
            "notify_on_move_sms_message",
            "notify_on_refuse_sms_message",
            "notify_as_reminder_sms_message",
        ],
    )


@implementer(INotificationSMS)
@adapter(IDexterityContent)
class NotificationSMS(object):
    """ """

    def __init__(self, context):
        self.context = context
