"""Top-level package for IO tools."""
# -*- encoding: utf-8 -*-

__author__ = """Mauro Amico"""
__email__ = "mauro.amico@gmail.com"
__version__ = "0.1.0"

import logging

from . import monkey

logger = logging.getLogger(__name__)
monkey.apply()
