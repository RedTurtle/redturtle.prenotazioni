Changelog
=========


2.2.4 (2023-11-30)
------------------

- Do not raise Unauthorized when translate title ical adapter.
  [cekk]


2.2.3 (2023-11-29)
------------------

- Fix message composition in manager notification.
  [cekk]


2.2.2 (2023-11-28)
------------------

- Set PrenotazioniFolder and PrenotazioneType as not searchable (types_not_searched).
  [cekk]
- Send ical also for manager notifications.
  [cekk]


2.2.1 (2023-11-22)
------------------

- Do not send the booking created email if auto_confirm is true and notify on confirm is true.
  [folix-01, cekk]


2.2.0 (2023-11-20)
------------------

- Fix sub BaseSlots whene some slots overlap
  [mamico]

- Compatibility with old code that use booking_types field in PrenotazioniFolder
  [mamico]

- Extend the booking duration limit to 180 min.
  [folix-01]

- Allow Bookings Manager to create, move the bookings and create the vacations.
  [folix-01]

- [BREAKING CHANGE] Convert booking types to c.t.
  [folix-01]

- Change bookings default limit to 0.
  [folix-01]

- Fix Bookings Manager permission in according to expected behavior
  [folix-01]

- Add booking_refuse_message to Prenotazione stringinterp variables.
  [folix-01]
 
- Extended PrenotaizoniFolder email templates var list.
  [folix-01]

- Better handle overrides between years.
  [cekk]


2.1.5 (2023-11-10)
------------------

- Fix release (2.1.4 was already made).
  [cekk]


2.1.4 (2023-11-10)
------------------

- Fix week overrides when booking next year.
  [cekk]

- Bypass limit for out-of-office bookings.
  [cekk]


2.1.3 (2023-10-13)
------------------

- Resect hidden booking types from @booking-schema.
  [folix-01]


2.1.2 (2023-10-13)
------------------

- Add hidden booking types for operator use.
  [folix-01]


2.1.1 (2023-10-11)
------------------

- Sort gate slots in get_free_slots method to better handle also pauses.
  [cekk]


2.1.0 (2023-10-11)
------------------

- Add booking details to the export file.
  [folix-01]

- Change PrenotazioniFolder.cosa_serve field type to RichText.
  [folix-01]

- Utilizzare defaultFactory se il default è una funzione, altrimenti non viene
  eseguita nel momento corretto.
  [mamico]

- Rimosso searchabletext di prenotazioni doppio.
  [mamico]

- Aggiunto indexer per fiscalcode uppercase per
  fare ricerche case insensitive.
  [mamico]

- Remove Contributor from the package permissions map.
  [folix-01]

- Add configurable simultaneous bookings limit for the same user.
  [folix-01]

- Remove "immediate=True" from mailhost send in send_email_to_managers because can cause multiple sends when there are conflicts.
  [cekk]

- Better handle edge-case when a booking is created inside a pause (booking created before pause set in folder config).
  [cekk]

2.0.0 (2023-09-12)
------------------

- workaround per download prenotazioni, parametri in base64 sul path
  per gestire bug Volto
  [mamico]

- add xlsx tests
  [mamico]

- add booking description in @bookings
  [mamico]

- add booking_code field to IPrenotazione schema
  update locales
  [lucabel]

- Call booking url adapter on plone.stringinterp.adapters.ContextWrapper
  [foxli-01]

- Traduzioni
  [mamico]

- Restapi @booking-notify.
  [foxli-01]

2.0.0rc5 (2023-09-05)
---------------------

- Update locales.
  [foxli-01]


2.0.0rc4 (2023-09-05)
---------------------

- Add a dedicated role to manage the bookings.
  [folix-01]


2.0.0.rc2 (2023-08-31)
----------------------

- Show default gates as unavailable in get_gates method, if they are overrided.
  [cekk]
- Skip required field validation when add out of office bookings in @booking endpoint.
  [cekk]
- Only users with permission can add out of office bookings in @booking endpoint.
  [cekk]
- Fix slots overlap valiation on booking move
  [folix-01]

2.0.0.rc1 (2023-08-25)
----------------------

- Remove complexity in `same_day_booking_disallowed`` field: now you can set only *yes* or *no*.
  [cekk]

- duration in minutes instead of days
  [mamico]

- allow to add out-of-office in api (aka blocco prenotazione)
  [mamico]

2.0.0.dev5 (2023-08-21)
-----------------------

- Add logic to override pauses and gates.
  [daniele]

- Permit to force gate / duration to operator (restapi add booking)
  [mamico]

- Changes required to migrate the old bookings.
  [folix-01]


- Allow to override also gates and pauses.
  [cekk]

- Remove unused unavailable_gates field.
  [cekk]

2.0.0.dev4 (2023-08-11)
-----------------------

- Moved contacts fields to a dedicated behavior.
  [daniele]

- Tabs/fields reordering for the booking folder.
  [daniele]

- fix date in @@download
  [mamico]

- fix tz in pause
  [mamico]

- skip email to manager on block/vacation creation
  [mamico]

- Manage timezone in booking dates. (upgrade step)
  [cekk]

- Fix: only valid interval in the subtraction slots operation.
  [mamico]

- Fix boking code uniqueness
  [folix-01]

- Fix default start/end time for search @bookings
  [mamico]

- Add @vacation rest api
  [mamico]

- Customized status message in prenotazione_print.pt based on review_state.
  [cekk]

- Add @booking-move restapi
  [mamico]

- Extend @@bookings search view parameters list.
  [folix-01]

- Added event handler on booking creation to send email to managers.
  [daniele]

- Rename routes:
  months-slots => available-slots
  prenotazione-schema => booking-schema
  @@download_reservation => @@download/bookings.xlsx
  [cekk] [mamico]


2.0.0.dev3 (2023-07-20)
-----------------------

- Handle contentrules by the plone events and do not use contentrules anymore.
  [folix-01]
- Change "day" type in week_table (TODO: need an upgrade step?).
  [mauro]

2.0.0.dev2 (2023-06-30)
-----------------------

- reorganize backend form
  [mamico]

- booking_type filter in @months-slots
  [mamico]

- Register adapters for IMailFromFieldAction for both Site root and dx containers.
  [cekk]

2.0.0.dev1 (2023-06-12)
-----------------------

- Add Booking restapi
  [mamico]

- Fix Plone6 compatibility.
  [cekk]

- Removed unused type PrenotazioniFolderContainer.
  [cekk]

- Added endpoint to get booking schema.
  [daniele]

- Avoid change gate, booking date, booking end from /edit;
  this would allow you to skip the checks;
  Fix profile registration name;
  [lucabel]

- Add @bookings endpoint to get booking items for a user
  [foxtrot-dfm1]

- Add a new endpoint to get booking details. (#40442).
  [daniele]

- Add autoconfirm content rule to profile.
  [foxtrot-dfm1]

- Added field "cosa_serve" (#40445).
  [daniele]

- Refactor booking delete machinery and remove unused token.
  [cekk]

- Add DELETE endpoint for booking.
  [cekk]

- Add new field that allows to override week schedule for a certain date range.
  [cekk]

- Send iCal attachment on approved or moved booking.
  [cekk]

1.7.1 (2023-03-28)
------------------

- Add plone5 profile to setup.
  [foxtrot-dfm1]


1.7.0 (2023-03-24)
------------------

- Remove sort order on week-legend table (#33584).
  [foxtrot-dfm1]
- RestAPI endpoint to have available week slots.
  [foxtrot-dfm1]

- Plone 6 support
  [mamico]


1.6.5 (2023-02-06)
------------------

- Fix the upgrade step of release 1.6.4
  [foxtrot-dfm1]

1.6.4 (2023-02-06)
------------------

- Fix the upgrade step of release 1.6.1
  [foxtrot-dfm1]


1.6.3 (2023-02-01)
------------------

- Fix cookies encoding
  [foxtrot-dfm1]


1.6.2 (2023-01-30)
------------------

- Handle prenotation type passed by url.
  [foxtrot-dfm1]


1.6.1 (2023-01-11)
------------------

- Handle confirmed state instead of published.
  [cekk]


1.6.0 (2023-01-10)
------------------

- The workflow state 'public' of prenotazioni_workflow was renamed to 'confirmed'
  [foxtrot-dfm1]
- Show review state column of prenotations (#37119)
  [foxtrot-dfm1]

1.5.7 (2022-12-29)
------------------

- updated mail sent to the final user to show report with delete option for accepted booking.
  [daniele]

1.5.6 (2022-12-06)
------------------

- fix: now handle differente dst in prenotazione_add booking_date.
  [cekk]


1.5.5 (2022-12-06)
------------------

fix: booking hour.
  [cekk]

1.5.4 (2022-12-06)
------------------

- fix: show actual booking hour un prenotazione_add view.
  [cekk]


1.5.3 (2022-12-06)
------------------

- chore: updated time label of booking add view
  [sara]


1.5.2 (2022-11-30)
------------------

- fix: export all visible fields in the ods report.
  [cekk]


1.5.1 (2022-11-16)
------------------

- fix: fixed booking labels [sara]


1.5.0 (2022-11-14)
------------------

- [BREAKING CHANGE] Remove recaptcha dependency and use collective.honeypot. UNINSTALL plone.formwidget.recaptcha before upgrading to this version.
  [cekk]


1.4.4 (2022-09-30)
------------------

- Fix upgrade-step.
  [cekk]


1.4.3 (2022-08-01)
------------------

- Add caching profile and enable it on install.
  [cekk]


1.4.2 (2022-05-22)
------------------

- Disable check_valid_fiscalcode constraint.
  [cekk]


1.4.1 (2022-05-04)
------------------

- Standardize fields between schema and creation form.
  [cekk]
- Improve extensibility of add form and required fields.
  [cekk]
- Handle (do not broke) non existent fiscalcode member field.
  [cekk]

1.4.0 (2022-01-13)
------------------

- Better manage fiscalcode.
  [cekk]
- Add github actions for code quality and fix black/zpretty/flake8 linting.
  [cekk]

1.3.5 (2021-10-15)
------------------

- [new] Added field "Note prenotante" e "Note del personale" inside the
  exported .ods file.
  [arsenico13]


1.3.4 (2021-09-08)
------------------

- [chg] only editor/manager can view booking data
  [mamico]
- [fix] fix check title on vacation booking
  [eikichi18]


1.3.3 (2021-08-09)
------------------

- [chg] autofill data from user context
  [mamico]


1.3.2 (2021-06-17)
------------------

- Prevented booking without gate
  [eikichi18]


1.3.1 (2021-06-14)
------------------

- Booking tipology as required
  [eikichi18]


1.3.0 (2021-06-07)
------------------

- [fix] translations
  [nzambello]
- [chg] prenotazioni slot as required
  [nzambello]
- [fix] slot prenotazione search button
  [nzambello]


1.2.0 (2021-05-31)
------------------

- [fix] handle reservation move without any gate set
  [cekk]
- [new] dependency with collective.z3cform.datagridfield>=2.0
  [cekk]

1.1.8 (2021-05-27)
------------------

- [fix] project urls in setup.py


1.1.7 (2021-05-27)
------------------

- [fix] changelog syntax
- [chg] project urls in setup.py


1.1.6 (2021-04-26)
------------------

- [fix] fix reservation download. ods writer can't cast none to empty string


1.1.5 (2021-04-26)
------------------

- [fix] force gate on authenticated reservation
- [fix] fix slot dimension in case of confirmed reservation
- [fix] Reindex subject on move
- [fix] download reservation after search give error calculating review_state


1.1.4 (2021-03-10)
------------------

- [fix] fix translations
- [chg] change prenotazioni search adding phone number and removing state
- [fix] fix problem with sending mail if mail not compiled
- [fix] allow to not use not required fields
  [lucabel]

1.1.3 (2021-02-22)
------------------

- [fix] fix search reservation accessing by gate icon


1.1.2 (2021-02-22)
------------------

- [chg] change 'sportello' label with 'postazione'
- [fix] now we can handle more gates and layout is safe
- [fix] fix insufficient permission deleting reservation
- [fix] pauses are spread over more gate if more gate are available
- [fix] hide "download" link in search reservation print


1.1.1 (2021-02-19)
------------------

- [chg] tuning permission to allow reader to see everything
- [chg] tuning css for mobile
- [new] add pause to prenotazioni folder
- [chg] add some accessibility to prenotazioni folder
- [new] add logic to delete reservation using a link sendable by mail

1.1.0 (2020-12-15)
------------------

- feat: tooltip on add button
  [nzambello]


1.0.3 (2020-12-10)
------------------

- Fix return url when click Cancel button.
  [cekk]


1.0.2 (2020-12-09)
------------------

- Changed fields order for prenotazione ct.
  [daniele]

1.0.1 (2020-12-09)
------------------

- Added logic to generate booking code on the fly.
  This code is calculated on the basis of the booking date and time.
  [daniele]
- Add new stringinterp for prenotazione print url and update contentrules.
  [cekk]
- Added fiscal code field to required fields. Added widget for visible fields.
  Updated views and templates.
  [daniele]

1.0.0 (2020-11-23)
------------------

- Initial release.
  [cekk]
