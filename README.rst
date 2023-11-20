
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
- hidden booking types for the internal usage
- more then one gate
- booking vacations
- custom duration for booking types
- week schedule for morning and afternoon time tables

Creating the hidden booking types
---------------------------------

You can hide your booking types from simple and anonymous users by using the 'Hidden Booking' flag
in your booking types definition. This way, it will only be available to users with the 'Bookings Manager'
permission. This feature may be useful if you want to restrict booking types for internal corporate use.

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


You can create your own email templates for the booking events(confirm, refuse, create, delete).
The temlates are being saved in the PrenotazioniFolder object.

The template variables list:

* ``${title}`` - booking title.
* ``${booking_gate}`` - booking gate.
* ``${booking_human_readable_start}`` - booking human readable start.
* ``${booking_date}`` - booking date.
* ``${booking_end_date}`` - booking end date.
* ``${booking_time}`` - booking time.
* ``${booking_time_end}`` - booking time end.
* ``${booking_code}`` - booking code.
* ``${booking_type}`` - booking type.
* ``${booking_print_url}`` - booking print url.
* ``${booking_url_with_delete_token}`` - booking url with delete token.
* ``${booking_user_phone}`` - booking user phone.
* ``${booking_user_email}`` - booking user email.
* ``${booking_user_details}`` - booking user details.
* ``${booking_office_contact_phone}`` - booking office contact phone.
* ``${booking_office_contact_pec}`` - booking office contact pec.
* ``${booking_office_contact_fax}`` - booking office contact fax.
* ``${booking_how_to_get_to_office}`` - booking how to get to office.
* ``${booking_office_complete_address}`` - booking office complete address.
* ``${booking_user_details}`` - booking user details
* ``${booking_requirements}`` - booking requeirements.
* ``${prenotazioni_folder_title}`` - prenotazioni folder title.
* ``${booking_user_details}`` - booking details.
* ``${booking_requirements}`` - booking_requirements
* ``${prenotazioni_folder_title}`` - PrenotazioniFolder title


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


MOVE
~~~~

This endpoint allows to move a booking by its UID to a different date/time slot.

Example::

    curl http://localhost:8080/Plone/++api++/<booking_folder_path>/@booking-move \
        -X POST \
        -H 'Accept: application/json' \
        -H 'Content-Type: application/json' \
        -d '{
            "booking_date": "2023-05-23T09:00:00+02:00",
            "booking_id": "<booking UID>",
        }'


@prenotazione
-------------

Leave for compatibility reasons (identical to `@booking`'s GET). Could be removed in future.

Example::

   curl http://localhost:8080/Plone/@prenotazione?uid=<booking UID> -H 'Accept: application/json'

Response, see: @booking

@vacation
---------

POST
~~~~

This endpoint allows to create a new vacation.

Example::

    curl http://localhost:8080/Plone/++api++/<booking_folder_path>/@vacation \
        -X POST \
        -H 'Accept: application/json' \
        -H 'Content-Type: application/json' \
        -d '{
            "start": "2023-05-23T09:00:00+02:00",
            "end": "2023-05-23T10:00:00+02:00",
            "gate": "gate A",
            "title": "vacation"
        }'


@available-slots
----------------

Endpoint that need to be called on a PrenotazioniFolder.
It returns the list of all available slots based on some parameters.

An available slot is the first free time on each hour slot (each day is split in 1h slots).

By default (without parameters) the endpoint returns available slots for the current month, starting from today.

Parameters:

- **start** a start date. If not given, the start will be today.
- **end** an end date. If not given, the end will be the last day of current month.


Example::

   curl -i http://localhost:8080/Plone/folder/@available-slots -H 'Accept: application/json'

Response::

    {
        "@id": "http://localhost:8080/Plone/folder/@available-slots",
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

   curl -i http://localhost:8080/Plone/folder/@available-slots?start=2023-04-12 -H 'Accept: application/json'

Response::

    {
        "@id": "http://localhost:8080/Plone/folder/@available-slots",
        "items": [
            '2023-04-17T07:00:00',
            '2023-04-17T08:00:00',
            '2023-04-17T09:00:00',
            '2023-04-24T07:00:00',
            '2023-04-24T08:00:00',
            '2023-04-24T09:00:00'
        ]
    }

@booking-schema
--------------------

Endpoint that need to be called on a PrenotazioniFolder.
It returns the list of all fields to fill in for the booking.

The booking date is passed via querystring (e.g ?booking_date=2023-04-13+10%3A00')

Example::

   curl -i -X GET 'http://localhost:8080/Plone/prenotazioni/@prenotazione-schema?booking_date=2023-05-15T13:00:00' -H 'Accept: application/json'

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

- **SearchableText**: The SearchableText of content.
- **from**: The start date of research.
- **to**: The end date of research.
- **gate**: The booking gate.
- **userid**: The userid(basically it is the fiscalcode). Allowed to be used by users having the 'redturtle.prenotazioni: search prenotazioni' permission.
- **booking_type**: The booking_type, available values are stored in 'redturtle.prenotazioni.booking_types' vocabulary.
- **review_state**: The booking status, one of: 'confirmed', 'refused', 'private', 'pending'

Example::

   curl -i http://localhost:8080/Plone/@bookings?from=10-10-2023&to=20-10-2023&gate=Gate1&userid=user1&booking_type=type1&SearchableText=text1 \
     -H 'Accept: application/json'

Response::

    {
        "@id": "http://localhost:8080/Plone/folder/@bookings",
        "items": [
             {
                "title": "Booking Title",
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


@booking-notify
---------------

Endpoint that fires the confirm email to user


Example::

   curl -i http://localhost:8080/Plone/booking_folder/@booking-notify/<booking UID> \
     -H 'Accept: application/json'


If the user is not logged in, the endpoint will return a 401 error.

Response::
    HTTP 200 OK


@day-busy-slots
---------------

Endpoint that returns a list of busy slots and pauses based on the passed date

Parameters:

- **date**: Date

Example::

    curl -i  "http://localhost:8080/Plone/prenotazioni_folder/@day-busy-slots?date=2023/05/22"\
        -H 'Accept: application/json'\

Response::

    {
        "@id": "http://localhost:8080/Plone/prenotazioni_folder/@day-busy-slots",
        "bookings": {
            "gate1":
                [
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
                    },
                    ...
                ],
            "gate2":
                [
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
                    },
                    ...
                ]
        },
        "pauses": [
            {
                "start": "2023-05-22T07:15:00+00:00",
                "stop": "2023-05-22T08:30:00+00:00"
            },
            ...
        ]
    }

Special Views
==============

@@download/bookings.xlsx
------------------------

This view allows to download the bookings filtered by passed parameters

- **text**: The SearchableText of content.
- **from**: The start date of research.
- **to**: The end date of research.
- **gate**: The booking gate.
- **userid**: The userid(basically it is the fiscalcode). Allowed to be used by users having the 'redturtle.prenotazioni: search prenotazioni' permission.
- **booking_type**: The booking_type, available values are stored in 'redturtle.prenotazioni.booking_types' vocabulary.
- **review_state**: The booking status, one of: 'confirmed', 'refused', 'private', 'pending'


Example::
    curl -i http://localhost:8080/Plone/folder/@@download/bookings.xlsx?text=Text&review_state=confirmed&gate=Gate1&start=2010-10-10&end=2025-10-10&booking_type=Type1

Response::
    Binary file

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
