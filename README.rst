
.. image:: https://img.shields.io/pypi/v/redturtle.prenotazioni.svg
    :target: https://pypi.org/project/redturtle.prenotazioni/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/pyversions/redturtle.prenotazioni.svg?style=plastic
    :target: https://pypi.org/project/redturtle.prenotazioni/
    :alt: Supported - Python Versions

.. image:: https://img.shields.io/pypi/dm/redturtle.prenotazioni.svg
    :target: https://pypi.org/project/redturtle.prenotazioni/
    :alt: Number of PyPI downloads

.. image:: https://img.shields.io/pypi/l/redturtle.prenotazioni.svg
    :target: https://pypi.org/project/redturtle.prenotazioni/
    :alt: License

.. image:: https://github.com/RedTurtle/redturtle.prenotazioni/actions/workflows/tests.yml/badge.svg
    :target: https://github.com/RedTurtle/redturtle.prenotazioni/actions
    :alt: Tests

.. image:: https://coveralls.io/repos/github/RedTurtle/redturtle.prenotazioni/badge.svg?branch=master
    :target: https://coveralls.io/github/RedTurtle/redturtle.prenotazioni?branch=master
    :alt: Coverage

======================
redturtle.prenotazioni
======================

A **booking product for Plone** which allows to reserve time slots throughout the week.

.. contents::

Installation
============

Add **redturtle.prenotazioni** to the egg section of your instance:

::

  [instance]
  eggs=
        ...
        redturtle.prenotazioni

To avoid spam, there is a background validation with `collective.honeypot`_ .

.. _collective.honeypot: https://pypi.org/project/collective.honeypot


With a version of `plone.app.dexterity` lower than 3.* (ie Plone 5.2) you need to add
`collective.dexteritytextindexer`_ as requirement.

::

    [instance]
    eggs=
        ...
        redturtle.prenotazioni
        collective.dexteritytextindexer

.. _collective.dexteritytextindexer: https://pypi.org/project/collective.dexteritytextindexer

Introduction
============

This product introduces two new `content types`_ to your Plone site:

.. _content types: http://developer.plone.org/content/types.html

- `Booking`
- `Booking Folder`

Booking content
---------------

**Booking** is a `content type` used to store information about reservation.

The product interface provides a way to add new booking elements, by clicking on one of the plus signs available in the slots calendar.

Each booking element once created is storerd into its own **Booking Folder**.


Booking Folder content
----------------------

**Booking Folder** is a folderish content type which store your **Booking** objects.


Using redturtle.prenotazioni
============================

Creating a new Booking Folder
-----------------------------

If the product is correctly installed the **Booking Folder** entry is available on the `add new` action menu.

You can configure:

- more then one gate
- booking vacations
- custom duration for booking types
- week schedule for morning and afternoon time tables

Creating a new booking content
------------------------------

Anonymous and authenticated users are allowed to add new booking content
by clicking on the plus signs on the default booking folder view.

After its creation the slot will be displayed as "busy" for anonymous user
and the slot won't be available anymore.

Back-end users can see and manage the reservation according to the assigned Plone roles.


Workflow
--------

The product comes with its own workflow "prenotazioni_workflow".

Here below a list of all the states available:

**Private**: booking object initial state:

* `submit` (Automatic transition to pending)

**Pending**

Transaction available:

* `publish` (to published)
* `refuse` (to refused)

**Published**

Transaction available:

* `refuse` (to refused)

**Refused**

Transaction available:

* `restore` (to pending)

Managers can confirm a Booking using workflow transitions.
The workflow transition triggers an email to be sent to the booker (see below).


Content Rules (mail notifications)
----------------------------------

There are additional content rules that can be used to notify booking owner when his booking has been created, accepted
or re-scheduled.

Rules are **NOT automatically** enabled in every Booking Folder.
If you want to send some notification, you only need to enable them from rules link in Booking folder.

If you set "Responsible email" field, an email will be sent each time a new Booking has been submitted.

The rules which are available by default:

* `booking-accepted` (Invia un'email all'utente quando la prenotazione è stata accettata)
* `booking-moved` (Invia un'email all'utente quando la data della prenotazione viene cambiata)
* `booking-created-user` (Invia un'email all'utente quando la prenotazione è stata creata)
* `booking-refuse` (Invia un'email all'utente quando la prenotazione è stata rifiutata)
* `booking-confirm` (Conferma automatica prenotazioni)

Vacations
---------

You can specify days when the Booking Folder will not accept
bookings.
Those days are called "Vacation days".

Vacation days can be specified compiling the "Vacation days"
field in the Booking Folder edit form.
Values are allowed in the format DD/MM/YYYY.
Instead of the year you can put an asterisk, in this case every here
the day DD of month MM will be considered a vacation day.

It is also possible to specify a vacation period
for a single gate using the vacation booking form with a link that you can see in the toolbar.


Searching
---------

Using the prenotazioni_search view it is possible to search
bookings within a given time interval.
You can also filter the results specifying a searchable text,
a gate or a review state.


Rest API
========

There are some endpoints useful to use this tool also with external frontends (like Volto).

@booking
--------

GET
~~~

This endpoint allows to retrieve a booking by its UID.

Example::

    curl http://localhost:8080/Plone/++api++/@booking/<booking UID> -H 'Accept: application/json'

Response::

    {
        "booking_code": "17E3E6",
        "booking_date": "2023-05-22T09:09:00",
        "booking_expiration_date": "2023-05-22T09:10:00",
        "booking_type": "SPID: SOLO riconoscimento \"de visu\" (no registrazione)",
        "company": null,
        "cosa_serve": null,
        "description": "",
        "email": "mario.rossi@example",
        "fiscalcode": "",
        "gate": "postazione2",
        "id": "mario-rossi",
        "phone": "",
        "staff_notes": null,
        "title": "Mario Rossi"
    }

POST
~~~~

This endpoint allows to create a new booking.

Example::

    curl http://localhost:8080/Plone/++api++/<booking_folder_path>/@booking \
        -X POST \
        -H 'Accept: application/json' \
        -H 'Content-Type: application/json' \
        -d '{
            "booking_date": "2023-05-23T09:00:00+02:00",
            "booking_type": "SPID: SOLO riconoscimento \"de visu\" (no registrazione)",
            "fields": [
                {"name": "fullname", "value": "Mario Rossi"},
                {"name": "email", "value": "mario.rossi@example"}
            ],
        }'

Response::

    {
        "booking_code": "17E3E6",
        "booking_date": "2023-05-22T09:09:00",
        "booking_expiration_date": "2023-05-22T09:10:00",
        "booking_type": "SPID: SOLO riconoscimento \"de visu\" (no registrazione)",
        "company": null,
        "cosa_serve": null,
        "description": "",
        "email": "mario.rossi@example",
        "fiscalcode": "",
        "gate": "postazione1",
        "id": "mario-rossi-1",
        "phone": "",
        "staff_notes": null,
        "title": "Mario Rossi"
    }

DELETE
~~~~~~

This endpoint allows to delete a booking by its UID.

Example::

    curl -X DELETE http://localhost:8080/Plone/++api++/@booking/<booking UID> -H 'Accept: application/json'

A booking can be deleted only if on of the following rules are satisfied:

- Anonymous user and booking has been created by an anonymous user
- Booking created by current logged-in user
- Current logged-in user has `redturtle.prenotazioni.ManagePrenotazioni` permission
- Booking has a date > today

@prenotazione
-------------

Leave for compatibility reasons (identical to `@booking`'s GET). Could be removed in future.

Example::

   curl http://localhost:8080/Plone/@prenotazione?uid=<booking UID> -H 'Accept: application/json'

Response, see: @booking

@week-slots
-----------

Endpoint that need to be called on a PrenotazioniFolder, and returns the combination of all busy and available slots of a week.
By default returns the current week, and if you pass a custom date in querystring, you will get the slots of that week.

Example::

   curl -i http://localhost:8080/Plone/folder/@week-slots -H 'Accept: application/json'

Response::

    {
        "@id": "http://localhost:8080/Plone/folder/@week-slots",
        "items": {
            '01-01-1970': {
                'busy_slots': [
                    'Gate': {
                        'start': '09:00',
                        'stop': '09:30'
                    ],
                    'Gate1': [],
                    ...
                },
                'free_slots': {
                    'Gate': [
                        'start': '09:30',
                        'stop': '12:00'
                    ],
                    'Gate1': [
                        'start': '09:00',
                        'stop': '12:00'
                    ],
                    ...
                }
            },
            ...
        }
    }

@month-slots
------------

Endpoint that need to be called on a PrenotazioniFolder.
It returns the list of all available slots of a single month.
An available slot is the first free time on each hour slot (each day is split in 1h slots).

By default (without parameters) the endpoint returns the current month, starting from today.

If a `date`` is passed via querystring, the endpoint returns date's month starting from date's day.


Example::

   curl -i http://localhost:8080/Plone/folder/@month-slots -H 'Accept: application/json'

Response::

    {
        "@id": "http://localhost:8080/Plone/folder/@month-slots",
        "items": [
            '2023-04-10T07:30:00',
            '2023-04-10T08:00:00',
            '2023-04-10T09:00:00',
            '2023-04-17T07:00:00',
            '2023-04-17T08:00:00',
            '2023-04-17T09:00:00',
            '2023-04-24T07:00:00',
            '2023-04-24T08:00:00',
            '2023-04-24T09:00:00'
        ]
    }


Example::

   curl -i http://localhost:8080/Plone/folder/@month-slots?date=2023-04-12 -H 'Accept: application/json'

Response::

    {
        "@id": "http://localhost:8080/Plone/folder/@month-slots",
        "items": [
            '2023-04-17T07:00:00',
            '2023-04-17T08:00:00',
            '2023-04-17T09:00:00',
            '2023-04-24T07:00:00',
            '2023-04-24T08:00:00',
            '2023-04-24T09:00:00'
        ]
    }

@prenotazione-schema
--------------------

Endpoint that need to be called on a PrenotazioniFolder.
It returns the list of all fields to fill in for the booking.

The booking date is passed via querystring (e.g ?form.booking_date=2023-04-13+10%3A00')

Example::

   curl -i -X GET 'http://localhost:8080/Plone/prenotazioni/@prenotazione-schema?form.booking_date=2023-05-15T13:00:00' -H 'Accept: application/json'

Response::

    {
        "booking_types": {
            "bookable": [],
            "unbookable": [
                {
                "duration": "60",
                "name": "Rilascio CIE"
              }
            ]
        },
        "fields": [
          {
            "desc": "Inserisci l'email",
            "label": "Email",
            "name": "email",
            "readonly": false,
            "required": false,
            "type": "text",
            "value": ""
          },
          {
            "desc": "Inserisci il numero di telefono",
            "label": "Numero di telefono",
            "name": "phone",
            "readonly": false,
            "required": false,
            "type": "text",
            "value": ""
          },
          {
            "desc": "Inserisci ulteriori informazioni",
            "label": "Note",
            "name": "description",
            "readonly": false,
            "required": false,
            "type": "textarea",
            "value": ""
          },
          {
            "desc": "Inserisci il codice fiscale",
            "label": "Codice Fiscale",
            "name": "fiscalcode",
            "readonly": false,
            "required": true,
            "type": "text",
            "value": ""
          },
          {
            "desc": "Inserire il nome completo",
            "label": "Nome completo",
            "name": "Nome",
            "readonly": false,
            "required": true,
            "type": "text",
            "value": ""
          }
        ]
    }

@bookings
---------

Endpoint that returns a list of own *Prenotazione* content by parameters

Parameters:

- **from**: The statrt date of research
- **to**: The end date of research

Example::

   curl -i http://localhost:8080/Plone/@bookings?from=10-10-2023&to=20-10-2023 \
     -H 'Accept: application/json'

Response::

    {
        "@id": "http://localhost:8080/Plone/folder/@bookings",
        "items": [
             {
                "booking_id": "abcdefgh1234567890",
                "booking_url": "https://url.ioprenoto.it/prenotazione/abcd",
                "booking_date": "2018-04-25T10:00:00",
                "booking_expiration_date": "2018-04-30T10:00:00",
                "booking_type": "Servizio di prova",
                "booking_room": "stanza-1",
                "booking_gate": "sportello-urp-polifunzionale",
                "booking_status": "confirmed",
                "booking_status_label": "Confermata",
                "booking_status_date": "2018-04-25T10:00:00",
                "booking_status_notes": "Prenotazione confermata",
                "userid": "FISCALCODE",
            },
            ...
            ],
          }
    }

    
If the user is not logged in, the endpoint will return a 401 error.

If the user has a special permission, the endpoint can be called with any `fiscalcode`::

  curl -i http://localhost:8080/Plone/@bookings/FISCALCODE?from=10-10-2023 \
     -H 'Accept: application/json'


How to develop
==============

Frontend
--------

There is a custom widget made in React and registered as bundle.
To develop it, you should do following steps:

First of all, enable nvm::

    > nvm use

Install dependencies::

    > yarn

Run webpack::

    > yarn start

This will start webpack with autoreload.
To see changes on your site, you need to enable development mode in Resources Registry in your Plone site, and enable CSS and js development of "week-table-overrides-widget-bundle" bundle.


When changes are ok, you need to make a production build::

    > yarn build

Contribute
==========

- Issue Tracker: https://github.com/RedTurtle/redturtle.prenotazioni/issues
- Source Code: https://github.com/RedTurtle/redturtle.prenotazioni


Notes
=====

**redturtle.prenotazioni** has been tested with Plone 5.2 and works with Python 3.

This is a merge from other two booking products:

- `rg.prenotazioni`__.
- `pd.prenotazioni`__.

__ https://github.com/PloneGov-IT/rg.prenotazioni/
__ https://github.com/PloneGov-IT/pd.prenotazioni/


Credits
=======

Developed with the support of:

* `Unione Reno Galliera`__

  .. image:: http://blog.redturtle.it/pypi-images/redturtle.prenotazioni/logo-urg.jpg/image_mini
     :alt: Logo Unione Reno Galliera

* `S. Anna Hospital, Ferrara`__

  .. image:: http://www.ospfe.it/ospfe-logo.jpg
     :alt: S. Anna Hospital - logo

* `Comune di Padova`__;

  .. image:: https://raw.githubusercontent.com/PloneGov-IT/pd.prenotazioni/master/docs/logo-comune-pd-150x200.jpg
     :alt: Comune di Padova's logo

All of them supports the `PloneGov initiative`__.

__ http://www.renogalliera.it/
__ http://www.ospfe.it/
__ http://www.padovanet.it/
__ http://www.plonegov.it/

Authors
=======

This product was developed by **RedTurtle Technology** team.

.. image:: https://avatars1.githubusercontent.com/u/1087171?s=100&v=4
   :alt: RedTurtle Technology Site
   :target: http://www.redturtle.it/
