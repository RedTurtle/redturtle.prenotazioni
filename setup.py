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
    version="1.3.1",
    description="An add-on for Plone",
    long_description=long_description,
    # Get more from https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: Addon",
        "Framework :: Plone :: 5.2",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords="Python Plone",
    author="Daniele Andreotti",
    author_email="daniele.andreotti@redturtle.it",
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
    python_requires="==2.7, >=3.6",
    install_requires=[
        "setuptools",
        # -*- Extra requirements: -*-
        "z3c.jbot",
        "plone.api>=1.8.4",
        "plone.restapi",
        "collective.contentrules.mailfromfield",
        "pyinter",
        "plone.formwidget.recaptcha",
        "collective.dexteritytextindexer",
        "collective.z3cform.datagridfield>=2.0",
        "pyexcel_ods3",
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
        ]
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    [console_scripts]
    update_locale = redturtle.prenotazioni.locales.update:update_locale
    """,
)
