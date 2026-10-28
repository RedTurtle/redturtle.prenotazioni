# -*- coding: utf-8 -*-
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from redturtle.prenotazioni import _
from zope import schema
from zope.component import adapter
from zope.interface import implementer
from zope.interface import provider


@provider(IFormFieldProvider)
class IPendingBookingsCleanup(model.Schema):
    """Automatic cleanup options for pending bookings."""

    pending_bookings_cleanup_enabled = schema.Bool(
        title=_(
            "pending_bookings_cleanup_enabled_label",
            default="Auto-manage old pending bookings",
        ),
        description=_(
            "pending_bookings_cleanup_enabled_help",
            default="Enable automatic processing of bookings that remain pending for too long.",
        ),
        required=False,
        default=False,
    )

    pending_bookings_cleanup_days = schema.Int(
        title=_(
            "pending_bookings_cleanup_days_label",
            default="Pending days threshold",
        ),
        description=_(
            "pending_bookings_cleanup_days_help",
            default="Bookings pending for more than this number of days will be processed.",
        ),
        required=False,
        default=5,
        min=1,
    )

    pending_bookings_cleanup_delete = schema.Bool(
        title=_(
            "pending_bookings_cleanup_delete_label",
            default="Delete instead of cancel",
        ),
        description=_(
            "pending_bookings_cleanup_delete_help",
            default="If enabled, matched bookings are deleted. If disabled, they are only moved to canceled state.",
        ),
        required=False,
        default=False,
    )

    pending_bookings_cleanup_notify_users = schema.Bool(
        title=_(
            "pending_bookings_cleanup_notify_users_label",
            default="Notify affected users",
        ),
        description=_(
            "pending_bookings_cleanup_notify_users_help",
            default="Send cancellation notifications to affected users when bookings are processed.",
        ),
        required=False,
        default=False,
    )

    model.fieldset(
        "pending_bookings_cleanup",
        label=_(
            "pending_bookings_cleanup_fieldset_label",
            default="Pending Bookings Cleanup",
        ),
        description=_(
            "pending_bookings_cleanup_fieldset_help",
            default="Configure automatic handling for old pending bookings.",
        ),
        fields=[
            "pending_bookings_cleanup_enabled",
            "pending_bookings_cleanup_days",
            "pending_bookings_cleanup_delete",
            "pending_bookings_cleanup_notify_users",
        ],
    )


@implementer(IPendingBookingsCleanup)
@adapter(IDexterityContent)
class PendingBookingsCleanup(object):
    """Behavior adapter for pending bookings cleanup options."""

    def __init__(self, context):
        self.context = context
