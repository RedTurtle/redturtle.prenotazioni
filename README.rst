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

There is a recaptcha validation for anonymous users.

You need to set recaptcha keys in **@@recaptcha-settings** control panel.

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
