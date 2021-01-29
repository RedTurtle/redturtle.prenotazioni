# -*- coding: utf-8 -*-
from datetime import date
from datetime import timedelta
from plone import api
from plone.memoize.view import memoize
from Products.CMFCore.utils import getToolByName
from redturtle.prenotazioni import _
from redturtle.prenotazioni.browser.base import BaseView
from redturtle.prenotazioni.browser.interfaces import IDontFollowMe
from redturtle.prenotazioni.utilities.urls import urlify
from six.moves import range
from zope.deprecation import deprecate
from zope.interface import implementer
from zope.schema.vocabulary import getVocabularyRegistry


@implementer(IDontFollowMe)
class View(BaseView):
    """ Display appointments this week
    """

    @property
    @memoize
    def translation_service(self):
        """ The translation_service tool
        """
        return getToolByName(self.context, "translation_service")

    @property
    @memoize
    def localized_time(self):
        """ Facade for context/@@plone/toLocalizedTime
        """
        return api.content.get_view(
            "plone", self.context, self.request
        ).toLocalizedTime

    def DT2time(self, value):
        """
        Converts a DateTime in to a localized time
        :param value: a DateTime object
        """
        return self.localized_time(value, time_only=True)

    def get_day_msgid(self, day):
        """ Translate the week day
        """
        return self.translation_service.day_msgid(day.isoweekday() % 7)

    @property
    @memoize
    @deprecate("Use the prenotazioni_context_state property instead")
    def user_can_manage(self):
        """ States if the authenticated user can manage this context
        """
        if api.user.is_anonymous():
            return False
        permissions = api.user.get_permissions(obj=self.context)
        return permissions.get("Modify portal content", False)

    @property
    @memoize
    @deprecate("Use the prenotazioni_context_state property instead")
    def user_can_view(self):
        """ States if the authenticated user can manage this context
        """
        if api.user.is_anonymous():
            return False
        if self.prenotazioni.user_can_manage:
            return True
        return u"Reader" in api.user.get_roles(obj=self.context)

    @property
    @memoize
    @deprecate("Use the prenotazioni_context_state property instead")
    def user_can_search(self):
        """ States if the user can see the search button
        """
        return self.prenotazioni.user_can_manage

    @property
    @memoize
    def day_period_macro(self):
        """ Which macro should I use to display a day period
        """
        prenotazione_macros = self.prenotazione_macros
        if self.prenotazioni.user_can_manage:
            return prenotazione_macros["manager_day_period"]
        if self.prenotazioni.user_can_view:
            return prenotazione_macros["manager_day_period"]
        return prenotazione_macros["anonymous_day_period"]

    @property
    @memoize
    def slot_macro(self):
        """ Which macro should I use to display the slot
        """
        prenotazione_macros = self.prenotazione_macros
        if self.prenotazioni.user_can_manage:
            return prenotazione_macros["manager_slot"]
        if self.prenotazioni.user_can_view:
            return prenotazione_macros["manager_slot"]
        return self.prenotazione_macros["anonymous_slot"]

    @property
    @memoize
    def periods(self):
        """ Return the periods
        """
        if self.prenotazioni.user_can_manage:
            return ("morning", "afternoon", "stormynight")
        else:
            return ("morning", "afternoon")

    @property
    @memoize
    def actual_date(self):
        """ restituisce il nome del mese e l'anno della data in request
        """
        day = self.request.get("data", "")
        try:
            day_list = day.split("/")
            data = date(int(day_list[2]), int(day_list[1]), int(day_list[0]))
        except (ValueError, IndexError):
            data = self.prenotazioni.today
        return data

    @property
    @memoize
    def actual_week_days(self):
        """ The days in this week
        """
        actual_date = self.actual_date
        weekday = actual_date.weekday()
        monday = actual_date - timedelta(weekday)
        return [monday + timedelta(x) for x in range(0, 7)]

    @property
    @memoize
    def actual_translated_month(self):
        """ The translated Full name of this month
        """
        return self.translation_service.month(self.actual_date.month)

    @property
    @memoize
    def prev_week(self):
        """ The actual date - 7 days
        """
        return (self.actual_date - timedelta(days=7)).strftime("%d/%m/%Y")

    @property
    @memoize
    def next_week(self):
        """ The actual date + 7 days
        """
        return (self.actual_date + timedelta(days=7)).strftime("%d/%m/%Y")

    @property
    @memoize
    def prev_week_url(self):
        """ The link to the previous week
        """
        qs = {"data": self.prev_week}
        qs.update(self.prenotazioni.remembered_params)
        return urlify(self.request.getURL(), params=qs)

    @property
    @memoize
    def next_week_url(self):
        """ The link to the next week
        """
        qs = {"data": self.next_week}
        qs.update(self.prenotazioni.remembered_params)
        return urlify(self.request.getURL(), params=qs)

    @property
    @memoize
    def toggle_columns_url(self):
        """ The link to enable/disable the columns
        """
        params = self.prenotazioni.remembered_params.copy()
        if (
            "disable_plone.leftcolumn" in params
            or "disable_plone.rightcolumn" in params
        ):  # noqa
            params.pop("disable_plone.leftcolumn", "")
            params.pop("disable_plone.rightcolumn", "")
        else:
            params["disable_plone.leftcolumn"] = 1
            params["disable_plone.rightcolumn"] = 1
        data = self.request.form.get("data", "")
        if data:
            params["data"] = data
        return urlify(self.request.getURL(), params=params)

    @memoize
    def get_search_gate_url(self, gate, day):
        """ Search a a gate
        """
        params = {"start": day, "end": day}
        vr = getVocabularyRegistry()
        voc = vr.get(self.context, "redturtle.prenotazioni.gates")

        try:
            params["gate"] = voc.getTerm(gate).token
        except LookupError:
            params["text"] = gate

        return urlify(
            self.context.absolute_url(), "@@prenotazioni_search", params=params
        )

    @memoize
    def show_day_column(self, day):
        """ Return True or False according to the fact that the column should
        be shown
        """
        if self.prenotazioni.user_can_manage:
            return True
        periods = self.prenotazioni.get_day_intervals(day)
        return bool(periods["day"])

    def get_foreseen_booking_time(self, day, slot):
        """ Return the foreseen booking time message
        """
        booking_url = self.prenotazioni.get_anonymous_booking_url(day, slot)
        message = _(
            "foreseen_booking_time",
            default=u"Foreseen booking time: ${booking_time}",
            mapping={"booking_time": booking_url["title"], "day": "{} {}".format(self.context.translate(self.get_day_msgid(day), domain="plonelocales"), day.strftime('%d'))},
        )
        return message

    def get_busy_message(self, day, slot):
        """ Return busy message
        """

        booking_url = self.prenotazioni.get_anonymous_booking_url(day, slot)
        message = _(
            "foreseen_busy_time",
            default=u"${booking_time}, Orario non disponibile",
            mapping={"booking_time": booking_url["title"]},
        )
        return message

    def get_prenotation_message(self, day, link):
        """ Return prenotation slot
        """
        """ Return the foreseen booking time message
        """

        message = _(
            "prenotation_slot_message",
            default=u"${day}, ore ${booking_time}",
            mapping={
                "booking_time": link['title'],
                "day": "{} {}".format(self.context.translate(self.get_day_msgid(day), domain="plonelocales"), day.strftime('%d'))
            },
        )
        return message

    def get_booked_prenotation_message(self, day, booking):
        """ Return prenotation slot
        """
        """ Return the foreseen booking time message
        """

        message = _(
            "booked_prenotation_message",
            default=u"${day}, ore ${booking_time}, prenotato da ${booked_by}, prenotazione: ${type_prenotation} durata: ${duration} minuti",
            mapping={
                "booking_time": booking.Date().strftime('%H:%M'),
                "day": "{} {}".format(self.context.translate(self.get_day_msgid(day), domain="plonelocales"), day.strftime('%d')),
                "booked_by": booking.Title(),
                "duration": (booking.getDuration().seconds // 60) % 60,
                "type_prenotation": booking.getTipologia_prenotazione()
            },
        )
        return message

    def __call__(self):
        """ Hide the portlets before serving the template
        """
        # self.request.set('disable_plone.leftcolumn', 1)
        # self.request.set('disable_plone.rightcolumn', 1)
        return super(View, self).__call__()
