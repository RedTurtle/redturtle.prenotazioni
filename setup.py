# -*- coding: utf-8 -*-
"""Installer for the redturtle.prenotazioni package."""

from setuptools import find_packages
from setuptools import setup

long_description = "\n\n".join(
    [
        open("README.rst").read(),
        open("CONTRIBUTORS.rst").read(),
        open("CHANGES.rst").read(),
    ]
)


setup(
    name="redturtle.prenotazioni",
    version="2.2.4",
    description="An add-on for Plone",
    long_description=long_description,
    # Get more from https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: Addon",
        "Framework :: Plone :: 5.2",
        "Framework :: Plone :: 6.0",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords="Python Plone",
    author="RedTurtle Technology",
    author_email="sviluppoplone@redturtle.it",
    url="https://github.com/redturtle/redturtle.prenotazioni",
    project_urls={
        "PyPI": "https://pypi.org/project/redturtle.prenotazioni",
        "Source": "https://github.com/redturtle/redturtle.prenotazioni",
        "Tracker": "https://github.com/redturtle/redturtle.prenotazioni/issues",
        # 'Documentation': 'https://redturtle.prenotazioni.readthedocs.io/en/latest/',
    },
    license="GPL version 2",
    packages=find_packages("src", exclude=["ez_setup"]),
    namespace_packages=["redturtle"],
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.8",
    install_requires=[
        "setuptools",
        # -*- Extra requirements: -*-
        "z3c.jbot",
        "plone.api>=1.8.4",
        "plone.restapi",
        "collective.contentrules.mailfromfield>=1.2.0",
        "pyinter",
        "collective.honeypot",
        "collective.z3cform.datagridfield>=2.0",
        "pyexcel-xlsx",
        "click",
        # FIXME: se si rimuove il profilo di caching da qui (perchè c'è?), si può togliere anche questo pin
        # 3.0.0a14 e successive richiedono plone.base che è solo su plone 6
        "plone.app.caching>=3.0.0a1",
    ],
    extras_require={
        "test": [
            "plone.app.testing",
            # Plone KGS does not use this version, because it would break
            # Remove if your package shall be part of coredev.
            # plone_coredev tests as of 2016-04-01.
            "plone.testing>=5.0.0",
            "plone.app.contenttypes",
            "plone.app.robotframework[debug]",
            "collective.MockMailHost",
            "freezegun",
        ],
        "app_io": [
            "bravado",
            "pytz",
        ],
        "plone5": ["collective.dexteritytextindexer"],
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    [console_scripts]
    update_locale = redturtle.prenotazioni.locales.update:update_locale
    app_io = redturtle.prenotazioni.scripts.app_io:main
    """,
)
