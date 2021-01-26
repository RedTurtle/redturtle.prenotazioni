# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.interface import Interface


class IRedturtlePrenotazioniLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IPause(Interface):
    """Merker interface that defines a pause fake type object"""
