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
def notify_on_submit_subject_default_factory(context):
    return getattr(context, "translate", translate)(
        _("notify_on_submit_subject_default_value", "Booking created ${title}")
    )


@provider(IContextAwareDefaultFactory)
def notify_on_submit_message_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_on_submit_message_default_value",
            "Booking ${booking_type} for ${booking_date} at ${booking_time} was created.<a href=${booking_print_url}>Link</a>",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_confirm_subject_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_on_confirm_subject_default_value",
            "Booking of ${booking_date} at ${booking_time} was accepted",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_confirm_message_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_on_confirm_message_default_value",
            "The booking${booking_type} for ${title} was confirmed! <a href=${booking_print_url}>Link</a>",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_move_subject_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_on_move_subject_default_value",
            "Modified the boolking date for ${title}",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_move_message_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_on_move_message_default_value",
            "The booking scheduling of ${booking_type} was modified."
            "The new one is on ${booking_date} at ${booking_time}. <a href=${booking_print_url}>Link</a>.",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_refuse_subject_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_on_refuse_subject_default_value",
            "Booking refused for ${title}",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_on_refuse_message_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_on_refuse_message_default_value",
            "The booking ${booking_type} of ${booking_date} at ${booking_time} was refused.",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_as_reminder_subject_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_as_reminder_subject_default_value",
            "You have the upcomming booking on ${booking_date}",
        )
    )


@provider(IContextAwareDefaultFactory)
def notify_as_reminder_message_default_factory(context):
    return getattr(context, "translate", translate)(
        _(
            "notify_as_reminder_message_default_value",
            'Booking details are available by the following <a href="${booking_pring_url}">link</a>',
        )
    )


@provider(IFormFieldProvider)
class INotificationEmail(model.Schema):
    notifications_email_enabled = schema.Bool(
        title=_(
            "notifications_email_enabled_label", default="Email notifications enabled."
        ),
        description=_(
            "notifications_email_enabled_help",
            default="Enable Email notifications.",
        ),
        default=True,
        required=False,
    )
    notify_on_submit_subject = schema.TextLine(
        title=_(
            "notify_on_submit_subject",
            default="Prenotazione created notification subject.",
        ),
        description=_("notify_on_submit_subject_help", default=""),
        defaultFactory=notify_on_submit_subject_default_factory,
        required=False,
    )
    notify_on_submit_message = schema.Text(
        title=_(
            "notify_on_submit_message",
            default="Prenotazione created notification message.",
        ),
        description=_("notify_on_submit_message_help", default=""),
        defaultFactory=notify_on_submit_message_default_factory,
        required=False,
    )
    notify_on_confirm_subject = schema.TextLine(
        title=_(
            "notify_on_confirm_subject",
            default="Prenotazione confirmed notification subject.",
        ),
        description=_("notify_on_confirm_subject_help", default=""),
        defaultFactory=notify_on_confirm_subject_default_factory,
        required=False,
    )
    notify_on_confirm_message = schema.Text(
        title=_(
            "notify_on_confirm_message",
            default="Prenotazione confirmed notification message.",
        ),
        description=_("notify_on_confirm_message_help", default=""),
        defaultFactory=notify_on_confirm_message_default_factory,
        required=False,
    )
    notify_on_move_subject = schema.TextLine(
        title=_(
            "notify_on_move_subject",
            default="Prenotazione moved notification subject.",
        ),
        description=_("notify_on_move_subject_help", default=""),
        defaultFactory=notify_on_move_subject_default_factory,
        required=False,
    )
    notify_on_move_message = schema.Text(
        title=_(
            "notify_on_move_message",
            default="Prenotazione moved notification message.",
        ),
        description=_("notify_on_move_message_help", default=""),
        defaultFactory=notify_on_move_message_default_factory,
        required=False,
    )
    notify_on_refuse_subject = schema.TextLine(
        title=_(
            "notify_on_refuse_subject",
            default="Prenotazione refused notification subject.",
        ),
        description=_("notify_on_refuse_subject_help", default=""),
        defaultFactory=notify_on_refuse_subject_default_factory,
        required=False,
    )
    notify_on_refuse_message = schema.Text(
        title=_(
            "notify_on_refuse_message",
            default="Prenotazione created notification message.",
        ),
        description=_("notify_on_refuse_message_help", default=""),
        defaultFactory=notify_on_refuse_message_default_factory,
        required=False,
    )
    notify_as_reminder_subject = schema.TextLine(
        title=_(
            "notify_as_reminder_subject",
            default="Booking reminder subject.",
        ),
        description=_("notify_as_reminder_subject_help", default=""),
        defaultFactory=notify_as_reminder_subject_default_factory,
        required=False,
    )
    notify_as_reminder_message = schema.Text(
        title=_(
            "notify_as_reminder_message",
            default="Booking reminder message.",
        ),
        description=_("notify_as_reminder_message", default=""),
        defaultFactory=notify_as_reminder_message_default_factory,
        required=False,
    )

    model.fieldset(
        "Prenotazioni Email Templates",
        label=_(
            "prenotazioni_email_templates_label",
            default="Testo delle email di notifica",
        ),
        fields=[
            "notify_on_submit_subject",
            "notify_on_submit_message",
            "notify_on_confirm_subject",
            "notify_on_confirm_message",
            "notify_on_move_subject",
            "notify_on_move_message",
            "notify_on_refuse_subject",
            "notify_on_refuse_message",
        ],
    )


@implementer(INotificationEmail)
@adapter(IDexterityContent)
class NotificationEmail(object):
    """ """

    def __init__(self, context):
        self.context = context
