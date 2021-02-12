# -*- coding: utf-8 -*-
from zope.component import Interface
from zope.interface import implementer
from plone import api
from plone.api.exc import MissingParameterError
from zope.annotation.interfaces import IAnnotations
from redturtle.prenotazioni.config import DELETE_TOKEN_KEY
from datetime import datetime
import jwt
from jwt.exceptions import DecodeError


class IDeleteTokenProvider(Interface):
    """ Interface for a reservation
    """


@implementer(IDeleteTokenProvider)
class DeleteToken(object):
    def __init__(self, context):
        self.context = context
        self.registry_record = "redturtle.prenotazioni.secret_cancellazione"
        self.algorithm = "HS256"

    def generate_token(self, expiration=None, payload={}):
        """
        @param obj: the reservation
        @param time: eventual expiration date or time
        @return a new JWT token
        """
        secret = api.portal.get_registry_record(
            self.registry_record, default=None
        )
        if not secret:
            """
            We miss a parameter
            """
            raise MissingParameterError("Secret is missing")

        if expiration:
            # Right now not handled
            payload.update({"expiration": expiration.isoformat()})
        else:
            # we set as a default midnight of the previous day
            payload.update({"expiration": None})

        encoded = jwt.encode(payload, secret, algorithm=self.algorithm)
        return encoded

    def decrypt_token(self, token):
        """
        @param token: the JWT token we have to decrypt
        @return: the JWT token payload
        """
        secret = api.portal.get_registry_record(
            self.registry_record, default=None
        )
        if not secret:
            """
            We miss a parameter
            """
            raise MissingParameterError("Secret is missing")
        decoded = jwt.decode(token, secret, algorithms=self.algorithm)
        return decoded

    def is_valid_token(self, token):
        """
        @param token: we get a token to validate
        @return: 'valid' or 'invalid' or 'expired'. We decide to pass a different
                 state for an invalid token if it's invalid due to expiration
        """
        try:
            payload = self.decrypt_token(token)
        except DecodeError:
            return "invalid"

        annotations = IAnnotations(self.context)
        stored_token = annotations.get(DELETE_TOKEN_KEY, None)

        # We store an encrypted data. The method produce a bytes string, so we
        # need to decode it to have a string rapresentation
        if stored_token != token:
            return "invalid"

        if "expiration" in payload:
            # Evaluate if token is still valid.
            # Right now we don't do it but we make the next check:
            try:
                expiration = datetime.fromisoformat(payload["expiration"])
                now = datetime.now()
                if now > expiration:
                    return "expired"

            except Exception:
                # In any case, if we are not able to rebuild information, token
                # is invalid
                return "invalid"
            return "valid"
        else:
            # if stored_token == token and we don't check expiration, token is
            # valid
            return "valid"
        return "invalid"
