# -*- coding: utf-8 -*-
from plone.restapi.services import Service

# src/redturtle/prenotazioni/browser/prenotazione_add.py


class AddBooking(Service):
    """
    Add a new booking
    """

    def reply(self):
        # data, errors = self.extractData()
        # if errors:
        #     self.status = self.formErrorsMessage
        #     return

        required = self.context.required_booking_fields

        # la tipologia di una prenotazione deve essere sempre obbligatoria ticket: 19131
        if "booking_type" not in required:
            required.append("booking_type")

        # for field_id in self.fields.keys():
        #     if field_id in required and not data.get(field_id, ""):
        #         raise WidgetActionExecutionError(
        #             field_id, Invalid(_("Required input is missing."))
        #         )
        # if not data.get("booking_date"):
        #     raise WidgetActionExecutionError(
        #         "booking_date", Invalid(_("Please provide a booking date"))
        #     )

        # conflict_manager = self.prenotazioni.conflict_manager
        # if conflict_manager.conflicts(data):
        #     msg = _("Sorry, this slot is not available anymore.")
        #     raise WidgetActionExecutionError("booking_date", Invalid(msg))
        # if self.exceedes_date_limit(data):
        #     msg = _("Sorry, you can not book this slot for now.")
        #     raise WidgetActionExecutionError("booking_date", Invalid(msg))

        # obj = self.do_book(data)
        # if not obj:
        #     msg = _("Sorry, this slot is not available anymore.")
        #     api.portal.show_message(message=msg, type="warning", request=self.request)
        #     target = self.back_to_booking_url
        #     return self.request.response.redirect(target)
        # msg = _("booking_created")
        # api.portal.show_message(message=msg, type="info", request=self.request)
        # booking_date = data["booking_date"].strftime("%d/%m/%Y")

        # delete_token = IAnnotations(obj).get(DELETE_TOKEN_KEY, "")
        # params = {
        #     "data": booking_date,
        #     "uid": obj.UID(),
        #     "delete_token": delete_token,
        # }
        # target = urlify(
        #     self.context.absolute_url(),
        #     paths=["@@prenotazione_print"],
        #     params=params,
        # )
        # self.send_email_to_managers(booking=obj)

        # self.request.response.expireCookie(
        #     TIPOLOGIA_PRENOTAZIONE_NAME_COOKIE,
        #     path="/",
        # )

        # return self.request.response.redirect(target)
