Changelog
=========

1.7.5 (2023-12-13)
------------------

- Import fixes for #118: Fix sub BaseSlots whene some slots overlap.
  [cekk, mamico]


1.7.4 (2023-08-21)
------------------

- Add an export view customization for the booking contents.
  [folix-01]


1.7.3 (2023-07-26)
------------------

- Fix fuzzy translation.
  [cekk]


1.7.2 (2023-07-26)
------------------

- Customized status message in prenotazione_print.pt based on review_state.
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
