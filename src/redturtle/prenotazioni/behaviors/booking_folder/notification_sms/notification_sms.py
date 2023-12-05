# -*- coding: utf-8 -*-
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.i18n import translate
from zope.interface import implementer
from zope.interface import provider
from zope.schema.interfaces import IContextAwareDefaultFactory

from redturtle.prenotazioni import _


@provider(IContextAwareDefaultFactory)
def notify_on_submit_sms_message_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_on_submit_sms_message_default_value",
            "Booking ${booking_type} for ${booking_date} at ${booking_time} was created. ${booking_print_url}",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_confirm_sms_message_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_on_confirm_sms_message_default_value",
            "The booking${booking_type} for ${title} was confirmed! ${booking_print_url}",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_move_sms_message_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_on_move_sms_message_default_value",
            "The booking scheduling of ${booking_type} was modified."
            "The new one is on ${booking_date} at ${booking_time} {booking_print_url}",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_refuse_sms_message_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_on_refuse_sms_message_default_value",
            "The booking ${booking_type} of ${booking_date} at ${booking_time} was refused.",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_as_reminder_sms_message_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_as_reminder_sms_message_default_value",
            "Booking details are available by the following link: ${booking_pring_url}",
        )
    )


@provider(IFormFieldProvider)
class INotificationSMS(model.Schema):
    notifications_sms_enabled = schema.Bool(
        title=_(
            "notifications_sms_enabled_label", default="SMS notifications enabled."
        ),
        description=_(
            "notifications_sms_enabled_help",
            default="Enable SMS notifications.",
        ),
        default=True,
        required=False,
    )
    notify_on_submit_sms_message = schema.Text(
        title=_(
            "notify_on_submit_sms_message",
            default="Prenotazione created notification message.",
        ),
        description=_("notify_on_submit_sms_message_help", default=""),
        defaultFactory=notify_on_submit_sms_message_default_factory,
        required=False,
    )
    notify_on_confirm_sms_message = schema.Text(
        title=_(
            "notify_on_confirm_sms_message",
            default="Prenotazione confirmed notification message.",
        ),
        description=_("notify_on_confirm_sms_message_help", default=""),
        defaultFactory=notify_on_confirm_sms_message_default_factory,
        required=False,
    )
    notify_on_move_sms_message = schema.Text(
        title=_(
            "notify_on_move_sms_message",
            default="Prenotazione moved notification message.",
        ),
        description=_("notify_on_move_sms_message_help", default=""),
        defaultFactory=notify_on_move_sms_message_default_factory,
        required=False,
    )
    notify_on_refuse_sms_message = schema.Text(
        title=_(
            "notify_on_refuse_sms_message",
            default="Prenotazione created notification message.",
        ),
        description=_("notify_on_refuse_sms_message_help", default=""),
        defaultFactory=notify_on_refuse_sms_message_default_factory,
        required=False,
    )
    notify_as_reminder_sms_message = schema.Text(
        title=_(
            "notify_as_reminder_sms_message",
            default="Booking reminder message.",
        ),
        description=_("notify_as_reminder_sms_message", default=""),
        defaultFactory=notify_as_reminder_sms_message_default_factory,
        required=False,
    )

    model.fieldset(
        "SMS Notification Templates",
        label=_(
            "bookings_sms_templates_label",
            default="Booking SMS notifications",
        ),
        fields=[
            "notify_on_submit_sms_message",
            "notify_on_confirm_sms_message",
            "notify_on_move_sms_message",
            "notify_on_refuse_sms_message",
        ],
    )


@implementer(INotificationSMS)
@adapter(IDexterityContent)
class NotificationSMS(object):
    """ """

    def __init__(self, context):
        self.context = context
