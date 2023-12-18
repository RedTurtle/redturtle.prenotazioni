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
def notify_on_submit_appio_subject_default_factory(context):
    return api.portal.translate(
        _(
            "notify_on_submit_appio_subject_default_value",
            "[${prenotazioni_folder_title}] Booking created",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_submit_appio_message_default_factory(context):
    return api.portal.translate(
        _(
            "notify_on_submit_appio_message_default_value",
            "Booking ${booking_type} for ${booking_date} at ${booking_time} has been created.<br/><br/>You can see details and print a reminder following this [${booking_print_url}](link).",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_confirm_appio_subject_default_factory(context):
    return api.portal.translate(
        _(
            "notify_on_confirm_appio_subject_default_value",
            "[${prenotazioni_folder_title}] Booking of ${booking_date} at ${booking_time} was accepted",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_confirm_appio_message_default_factory(context):
    return api.portal.translate(
        _(
            "notify_on_confirm_appio_message_default_value",
            "The booking ${booking_type} for ${title} has been confirmed."
            "<br/><br/>You can see details and print a reminder following this [link](${booking_print_url}).",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_move_appio_subject_default_factory(context):
    return api.portal.translate(
        _(
            "notify_on_move_appio_subject_default_value",
            "[${prenotazioni_folder_title}] Booking date modified for ${title}",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_move_appio_message_default_factory(context):
    return api.portal.translate(
        _(
            "notify_on_move_appio_message_default_value",
            "The booking scheduling for ${booking_type} was modified."
            "<br/><br/>The new one is on ${booking_date} at ${booking_time}."
            "<br/><br/>You can see details and print a reminder following this [link](${booking_print_url}).",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_refuse_appio_subject_default_factory(context):
    return api.portal.translate(
        _(
            "notify_on_refuse_appio_subject_default_value",
            "[${prenotazioni_folder_title}] Booking refused for ${title}",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_refuse_appio_message_default_factory(context):
    return api.portal.translate(
        _(
            "notify_on_refuse_appio_message_default_value",
            "The booking ${booking_type} of ${booking_date} at ${booking_time} was refused.",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_as_reminder_appio_subject_default_factory(context):
    return api.portal.translate(
        _(
            "notify_as_reminder_appio_subject_default_value",
            "[${prenotazioni_folder_title}] Booking reminder on ${booking_date}",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_as_reminder_appio_message_default_factory(context):
    return api.portal.translate(
        _(
            "notify_as_reminder_appio_message_default_value",
            "This is an automatic reminder about your booking on ${date} for ${booking_type}."
            "<br/><br/>You can see details and print a reminder following this [link](${booking_print_url}).",
        )
    )


@provider(IFormFieldProvider)
class INotificationAppIO(model.Schema):
    notifications_appio_enabled = schema.Bool(
        title=_("notifications_appio_enabled_label", default="AppIO notifications"),
        description=_(
            "notifications_appio_enabled_help",
            default="Enable AppIO notifications.",
        ),
        default=False,
        required=False,
    )
    notify_on_submit_appio_subject = schema.TextLine(
        title=_(
            "notify_on_submit_subject",
            default="[Created] subject",
        ),
        description=_(
            "notify_on_submit_subject_help",
            default="The message subject when a booking has been created.",
        ),
        defaultFactory=notify_on_submit_appio_subject_default_factory,
        required=False,
    )
    notify_on_submit_appio_message = schema.Text(
        title=_(
            "notify_on_submit_message",
            default="[Created] message",
        ),
        description=_(
            "notify_on_submit_message_help",
            default="The message text when a booking has been created.",
        ),
        defaultFactory=notify_on_submit_appio_message_default_factory,
        required=False,
    )
    notify_on_confirm_appio_subject = schema.Text(
        title=_(
            "notify_on_confirm_subject",
            default="[Confirm] subject",
        ),
        description=_(
            "notify_on_confirm_subject_help",
            default="The message subject when a booking has been confirmed.",
        ),
        defaultFactory=notify_on_confirm_appio_subject_default_factory,
        required=False,
    )
    notify_on_confirm_appio_message = schema.Text(
        title=_(
            "notify_on_confirm_message",
            default="[Confirmed] message",
        ),
        description=_(
            "notify_on_confirm_message_help",
            default="The message text when a booking has been confirmed.",
        ),
        defaultFactory=notify_on_confirm_appio_message_default_factory,
        required=False,
    )
    notify_on_move_appio_subject = schema.Text(
        title=_(
            "notify_on_move_subject",
            default="[Move] subject",
        ),
        description=_(
            "notify_on_move_subject_help",
            default="The message subject when a booking has been moved.",
        ),
        defaultFactory=notify_on_move_appio_subject_default_factory,
        required=False,
    )
    notify_on_move_appio_message = schema.Text(
        title=_(
            "notify_on_move_message",
            default="[Move] message",
        ),
        description=_(
            "notify_on_move_message_help",
            default="The message text when a booking has been moved.",
        ),
        defaultFactory=notify_on_move_appio_message_default_factory,
        required=False,
    )
    notify_on_refuse_appio_subject = schema.Text(
        title=_(
            "notify_on_refuse_subject",
            default="[Refuse] subject",
        ),
        description=_(
            "notify_on_refuse_subject_help",
            default="The message subject when a booking has been refused.",
        ),
        defaultFactory=notify_on_refuse_appio_subject_default_factory,
        required=False,
    )
    notify_on_refuse_appio_message = schema.Text(
        title=_(
            "notify_on_refuse_message",
            default="[Refuse] message",
        ),
        description=_(
            "notify_on_refuse_message_help",
            default="The message text when a booking has been refused.",
        ),
        defaultFactory=notify_on_refuse_appio_message_default_factory,
        required=False,
    )
    notify_as_reminder_appio_subject = schema.Text(
        title=_(
            "notify_as_reminder_subject",
            default="[Reminder] subject",
        ),
        description=_(
            "notify_as_reminder_appio_subject_help",
            default="The message subject when a reminder will be sent.",
        ),
        defaultFactory=notify_as_reminder_appio_subject_default_factory,
        required=False,
    )
    notify_as_reminder_appio_message = schema.Text(
        title=_(
            "notify_as_reminder_message",
            default="[Reminder] message",
        ),
        description=_(
            "notify_as_reminder_message_help",
            default="The message text when a reminder will be sent.",
        ),
        defaultFactory=notify_as_reminder_appio_message_default_factory,
        required=False,
    )

    model.fieldset(
        "appio_notifications",
        label=_(
            "bookings_appio_templates_label",
            default="AppIO Notifications",
        ),
        description=_(
            "bookings_appio_templates_help",
            default="Set message text for all available notification events.",
        ),
        fields=[
            "notifications_appio_enabled",
            "notify_on_submit_appio_subject",
            "notify_on_submit_appio_message",
            "notify_on_confirm_appio_subject",
            "notify_on_confirm_appio_message",
            "notify_on_move_appio_subject",
            "notify_on_move_appio_message",
            "notify_on_refuse_appio_subject",
            "notify_on_refuse_appio_message",
            "notify_as_reminder_appio_subject",
            "notify_as_reminder_appio_message",
        ],
    )


@implementer(INotificationAppIO)
@adapter(IDexterityContent)
class NotificationAppIO(object):
    """ """

    def __init__(self, context):
        self.context = context


@provider(IFormFieldProvider)
class INotificationAppioBookingType(model.Schema):
    service_code = schema.Choice(
        title=_(
            "service_code_label",
            default="AppIO service code.",
        ),
        description=_(
            "service_code_help",
            default="AppIO service code related to the current booking type",
        ),
        required=False,
        vocabulary="redturtle.prenotazioni.appio_services",
    )


@implementer(INotificationAppioBookingType)
@adapter(IDexterityContent)
class NotificationAppIOBookingType(object):
    """ """

    def __init__(self, context):
        self.context = context
