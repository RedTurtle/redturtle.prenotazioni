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
def notify_on_submit_appio_subject_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_on_submit_appio_subject_default_value",
            "Booking ${booking_type} for ${booking_date} was created",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_submit_appio_message_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_on_submit_appio_message_default_value",
            "Booking ${booking_type} for ${booking_date} at ${booking_time} was created. ${booking_print_url}",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_confirm_appio_subject_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_on_confirm_appio_subject_default_value",
            "The booking$for ${title} was confirmed!",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_confirm_appio_message_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_on_confirm_appio_message_default_value",
            "The booking${booking_type} for ${title} was confirmed! ${booking_print_url}",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_move_appio_subject_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_on_move_appio_subject_default_value",
            "The booking scheduling of ${booking_type} was modified.",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_move_appio_message_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_on_move_appio_message_default_value",
            "The booking scheduling of ${booking_type} was modified."
            "The new one is on ${booking_date} at ${booking_time} {booking_print_url}",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_refuse_appio_subject_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_on_refuse_appio_subject_default_value",
            "The booking ${booking_type} was refused.",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_refuse_appio_message_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_on_refuse_appio_message_default_value",
            "The booking ${booking_type} of ${booking_date} at ${booking_time} was refused.",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_as_reminder_appio_subject_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_as_reminder_appio_subject_default_value",
            "You have an upcomming booking on ${booking_date}",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_as_reminder_appio_message_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_as_reminder_appio_message_default_value",
            "This is an automatic reminder about your booking "
            "on ${date} for ${booking_type}. If you need to see more infos "
            'or delete it, please access your booking details <a href="${booking_pring_url}">page</a>',
        )
    )


@provider(IFormFieldProvider)
class INotificationAppIo(model.Schema):
    notifications_appio_enabled = schema.Bool(
        title=_(
            "notifications_appio_enabled_label", default="AppIo notifications enabled."
        ),
        description=_(
            "notifications_appio_enabled_help",
            default="Enable AppIo notifications.",
        ),
        default=True,
        required=False,
    )
    notify_on_submit_appio_subject = schema.TextLine(
        title=_(
            "notify_on_submit_appio_subject",
            default="Prenotazione created notification subject.",
        ),
        description=_("notify_on_submit_appio_subject_help", default=""),
        defaultFactory=notify_on_submit_appio_subject_default_factory,
        required=False,
    )
    notify_on_submit_appio_message = schema.Text(
        title=_(
            "notify_on_submit_appio_message",
            default="Prenotazione created notification message.",
        ),
        description=_("notify_on_submit_appio_message_help", default=""),
        defaultFactory=notify_on_submit_appio_message_default_factory,
        required=False,
    )
    notify_on_confirm_appio_subject = schema.Text(
        title=_(
            "notify_on_confirm_appio_subject",
            default="Prenotazione confirmed notification subject.",
        ),
        description=_("notify_on_confirm_appio_subject_help", default=""),
        defaultFactory=notify_on_confirm_appio_subject_default_factory,
        required=False,
    )
    notify_on_confirm_appio_message = schema.Text(
        title=_(
            "notify_on_confirm_appio_message",
            default="Prenotazione confirmed notification message.",
        ),
        description=_("notify_on_confirm_appio_message_help", default=""),
        defaultFactory=notify_on_confirm_appio_message_default_factory,
        required=False,
    )
    notify_on_move_appio_subject = schema.Text(
        title=_(
            "notify_on_move_appio_subject",
            default="Prenotazione moved notification subject.",
        ),
        description=_("notify_on_move_appio_subject_help", default=""),
        defaultFactory=notify_on_move_appio_subject_default_factory,
        required=False,
    )
    notify_on_move_appio_message = schema.Text(
        title=_(
            "notify_on_move_appio_message",
            default="Prenotazione moved notification message.",
        ),
        description=_("notify_on_move_appio_message_help", default=""),
        defaultFactory=notify_on_move_appio_message_default_factory,
        required=False,
    )
    notify_on_refuse_appio_subject = schema.Text(
        title=_(
            "notify_on_refuse_appio_subject",
            default="Prenotazione created notification subject.",
        ),
        description=_("notify_on_refuse_appio_subject_help", default=""),
        defaultFactory=notify_on_refuse_appio_subject_default_factory,
        required=False,
    )
    notify_on_refuse_appio_message = schema.Text(
        title=_(
            "notify_on_refuse_appio_message",
            default="Prenotazione created notification message.",
        ),
        description=_("notify_on_refuse_appio_message_help", default=""),
        defaultFactory=notify_on_refuse_appio_message_default_factory,
        required=False,
    )
    notify_as_reminder_appio_subject = schema.Text(
        title=_(
            "notify_as_reminder_appio_subject",
            default="Booking reminder subject.",
        ),
        description=_("notify_as_reminder_appio_subject", default=""),
        defaultFactory=notify_as_reminder_appio_subject_default_factory,
        required=False,
    )
    notify_as_reminder_appio_message = schema.Text(
        title=_(
            "notify_as_reminder_appio_message",
            default="Booking reminder message.",
        ),
        description=_("notify_as_reminder_appio_message", default=""),
        defaultFactory=notify_as_reminder_appio_message_default_factory,
        required=False,
    )

    model.fieldset(
        "AppIo Notification Templates",
        label=_(
            "bookings_appio_templates_label",
            default="Booking AppIo notifications",
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


@implementer(INotificationAppIo)
@adapter(IDexterityContent)
class NotificationAppIo(object):
    """ """

    def __init__(self, context):
        self.context = context


@provider(IFormFieldProvider)
class INotificationAppioBookingType(model.Schema):
    service_code = schema.Choice(
        title=_(
            "service_code_label",
            default="AppIo service code.",
        ),
        description=_(
            "service_code_help",
            default="AppIO service code related to the current booking type",
        ),
        required=True,
        vocabulary="redturtle.prenotazioni.appio_services",
    )


@implementer(INotificationAppioBookingType)
@adapter(IDexterityContent)
class NotificationAppIoBookingType(object):
    """ """

    def __init__(self, context):
        self.context = context
