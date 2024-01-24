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
def notify_on_submit_subject_default_factory(context):
    return api.portal.translate(
        _(
            "notify_on_submit_subject_default_value",
            "[${prenotazioni_folder_title}] Booking created",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_submit_message_default_factory(context):
    return api.portal.translate(
        _(
            "notify_on_submit_message_default_value",
            "Booking ${booking_type} for ${booking_date} at ${booking_time} has been created.<br/><br/>You can see details and print a reminder following this <a href=${booking_print_url}>link</a>.",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_confirm_subject_default_factory(context):
    return api.portal.translate(
        _(
            "notify_on_confirm_subject_default_value",
            "[${prenotazioni_folder_title}] Booking of ${booking_date} at ${booking_time} was accepted",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_confirm_message_default_factory(context):
    return api.portal.translate(
        _(
            "notify_on_confirm_message_default_value",
            "The booking ${booking_type} for ${title} has been confirmed."
            "<br/><br/>You can see details and print a reminder following this <a href=${booking_print_url}>link</a>.",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_move_subject_default_factory(context):
    return api.portal.translate(
        _(
            "notify_on_move_subject_default_value",
            "[${prenotazioni_folder_title}] Booking date modified for ${title}",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_move_message_default_factory(context):
    return api.portal.translate(
        _(
            "notify_on_move_message_default_value",
            "The booking scheduling for ${booking_type} was modified."
            "<br/><br/>The new one is on ${booking_date} at ${booking_time}."
            "<br/><br/>You can see details and print a reminder following this <a href=${booking_print_url}>link</a>.",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_refuse_subject_default_factory(context):
    return api.portal.translate(
        _(
            "notify_on_refuse_subject_default_value",
            "[${prenotazioni_folder_title}] Booking refused for ${title}",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_refuse_message_default_factory(context):
    return api.portal.translate(
        _(
            "notify_on_refuse_message_default_value",
            "The booking ${booking_type} of ${booking_date} at ${booking_time} was refused.",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_as_reminder_subject_default_factory(context):
    return api.portal.translate(
        _(
            "notify_as_reminder_subject_default_value",
            "[${prenotazioni_folder_title}] Booking reminder on ${booking_date}",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_as_reminder_message_default_factory(context):
    return api.portal.translate(
        _(
            "notify_as_reminder_message_default_value",
            "This is an automatic reminder about your booking on ${date} for ${booking_type}."
            "<br/><br/>You can see details and print a reminder following this <a href=${booking_print_url}>link</a>.",
        )
    )


@provider(IFormFieldProvider)
class INotificationEmail(model.Schema):
    notifications_email_enabled = schema.Bool(
        title=_("notifications_email_enabled_label", default="Email notifications"),
        description=_(
            "notifications_email_enabled_help",
            default="Enable Email notifications.",
        ),
        default=True,
        required=False,
    )
    email_from = schema.TextLine(
        title=_("Email from"),
        description=_(
            'Insert an email address used as "from" in email notifications. '
            "Leave empty to use the default from set in the site configuration."
        ),
        required=False,
        default="",
    )
    notify_on_submit_subject = schema.TextLine(
        title=_(
            "notify_on_submit_subject",
            default="[Created] subject",
        ),
        description=_(
            "notify_on_submit_subject_help",
            default="The message subject when a booking has been created.",
        ),
        defaultFactory=notify_on_submit_subject_default_factory,
        required=False,
    )
    notify_on_submit_message = schema.Text(
        title=_(
            "notify_on_submit_message",
            default="[Created] message",
        ),
        description=_(
            "notify_on_submit_message_help",
            default="The message text when a booking has been created.",
        ),
        defaultFactory=notify_on_submit_message_default_factory,
        required=False,
    )
    notify_on_confirm_subject = schema.TextLine(
        title=_(
            "notify_on_confirm_subject",
            default="[Confirm] subject",
        ),
        description=_(
            "notify_on_confirm_subject_help",
            default="The message subject when a booking has been confirmed.",
        ),
        defaultFactory=notify_on_confirm_subject_default_factory,
        required=False,
    )
    notify_on_confirm_message = schema.Text(
        title=_(
            "notify_on_confirm_message",
            default="[Confirmed] message",
        ),
        description=_(
            "notify_on_confirm_message_help",
            default="The message text when a booking has been confirmed.",
        ),
        defaultFactory=notify_on_confirm_message_default_factory,
        required=False,
    )
    notify_on_move_subject = schema.TextLine(
        title=_(
            "notify_on_move_subject",
            default="[Move] subject",
        ),
        description=_(
            "notify_on_move_subject_help",
            default="The message subject when a booking has been moved.",
        ),
        defaultFactory=notify_on_move_subject_default_factory,
        required=False,
    )
    notify_on_move_message = schema.Text(
        title=_(
            "notify_on_move_message",
            default="[Move] message",
        ),
        description=_(
            "notify_on_move_message_help",
            default="The message text when a booking has been moved.",
        ),
        defaultFactory=notify_on_move_message_default_factory,
        required=False,
    )
    notify_on_refuse_subject = schema.TextLine(
        title=_(
            "notify_on_refuse_subject",
            default="[Refuse] subject",
        ),
        description=_(
            "notify_on_refuse_subject_help",
            default="The message subject when a booking has been refused.",
        ),
        defaultFactory=notify_on_refuse_subject_default_factory,
        required=False,
    )
    notify_on_refuse_message = schema.Text(
        title=_(
            "notify_on_refuse_message",
            default="[Refuse] message",
        ),
        description=_(
            "notify_on_refuse_message_help",
            default="The message text when a booking has been refused.",
        ),
        defaultFactory=notify_on_refuse_message_default_factory,
        required=False,
    )
    notify_as_reminder_subject = schema.TextLine(
        title=_(
            "notify_as_reminder_subject",
            default="[Reminder] subject",
        ),
        description=_(
            "notify_as_reminder_subject_help",
            default="The message subject when a reminder will be sent.",
        ),
        defaultFactory=notify_as_reminder_subject_default_factory,
        required=False,
    )
    notify_as_reminder_message = schema.Text(
        title=_(
            "notify_as_reminder_message",
            default="[Reminder] message",
        ),
        description=_(
            "notify_as_reminder_message_help",
            default="The message text when a reminder will be sent.",
        ),
        defaultFactory=notify_as_reminder_message_default_factory,
        required=False,
    )

    model.fieldset(
        "email_notifications",
        label=_(
            "bookings_email_templates_label",
            default="Email Notifications",
        ),
        description=_(
            "bookings_email_templates_help",
            default="Set message text for all available notification events.",
        ),
        fields=[
            "notifications_email_enabled",
            "email_from",
            "notify_on_submit_subject",
            "notify_on_submit_message",
            "notify_on_confirm_subject",
            "notify_on_confirm_message",
            "notify_on_move_subject",
            "notify_on_move_message",
            "notify_on_refuse_subject",
            "notify_on_refuse_message",
            "notify_as_reminder_subject",
            "notify_as_reminder_message",
        ],
    )


@implementer(INotificationEmail)
@adapter(IDexterityContent)
class NotificationEmail(object):
    """ """

    def __init__(self, context):
        self.context = context
