Changelog
=========


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
