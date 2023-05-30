'use strict';

function getCookie(name) {
  let cookie = {};
  document.cookie.split(';').forEach(function (el) {
    let [k, v] = el.split('=');
    cookie[k.trim('\'')] = v;
  });
  let cookie_str = cookie[name];

  if (cookie_str) {
    cookie_str = cookie_str.replace(/(^"|"$)/g, '');
  } else {
    return '';
  }

  return decodeURIComponent(cookie_str);
}

document.addEventListener('afterdatagridfieldinit', function () {
  var $ = window.jQuery;
  $('input[name$="widgets.day"]').attr('readonly', 'readonly');
});

document.addEventListener('DOMContentLoaded', function () {
  var $ = window.jQuery;
  var actionBook = $('#form-buttons-action_book');
  if (actionBook) {
    // console.log(actionBook);
    actionBook.addClass('context');
  }

  if ($('form.kssattr-formname-prenotazione_add').length > 0) {
    var TIPOLOGIA_PRENOTAZIONE_COOKIE = 'TipologiaPrenotazione_cookie';

    // function UnicodeDecodeB64(str) {
    //   return decodeURIComponent(atob(str));
    // }

    var arr = $('input[name^="form.widgets.booking_type"]');
    var booking_type_cookie = getCookie(TIPOLOGIA_PRENOTAZIONE_COOKIE);

    if (!booking_type_cookie) {
      return;
    }

    // sanitize type
    var preselcted_booking_type = booking_type_cookie
      .trim()
      .slice(1, booking_type_cookie.length - 1);

    for (var i = 0; i < arr.length; i++) {
      if (arr[i].value.includes(preselcted_booking_type)) {
        $(arr[i]).prop('checked', true);
      }
    };

    document.cookie =
      TIPOLOGIA_PRENOTAZIONE_COOKIE +
      '=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
  }
});
