require(["jquery"], function ($) {
  "use strict";

  // function rgdateinput() {
  //     if (!$.fn.dateinput) {
  //         return false;
  //     }

  //     function sync_inputs(backend, frontend) {
  //         backend.val(frontend.getValue('yyyy-mm-dd'));
  //     }

  //     $('.rg-dateinput').each(
  //         function (idx, el) {
  //             var frontend = jQuery(el).removeClass('rg-dateinput');
  //             var backend = frontend.clone().attr({ type: 'hidden' });
  //             jQuery('label[for="' + backend.attr('name') + '"] .formHelp').remove();
  //             frontend.after(backend);
  //             frontend.dateinput(
  //                 {
  //                     change: function () {
  //                         sync_inputs(backend, this);
  //                     }
  //                 }
  //             );
  //             frontend.removeClass('date');
  //             frontend.attr({ name: backend.attr('name') + Math.random() });
  //         }
  //     );
  // }
  // $(document).ready(rgdateinput);
  $(document).on("afterdatagridfieldinit", function () {
    $("input[name$='widgets.day']").attr("readonly", "readonly");
  });
  $(document).ready(function () {
    var actionBook = $("#form-buttons-action_book");
    if (actionBook) {
      console.log(actionBook);

      actionBook.addClass("context");
    }
  });

  $(document).ready(function() {
    const TIPOLOGIA_PRENOTAZIONE_COOKIE = "TipologiaPrenotazione_cookie";

    function UnicodeDecodeB64(str) {
      return decodeURIComponent(atob(str));
    }

    function getCookie(name) {
      let cookie = {};
      document.cookie.split(';').forEach(function(el) {
        let [k,v] = el.split('=');
        cookie[k.trim("'")] = v;
      })
      let cookie_str = cookie[name]

      if (cookie_str){
        cookie_str = cookie_str.replace(/(^"|"$)/g, '');
      } else {
        return '';
      }

      return decodeURIComponent(cookie_str);
    }

    if(!$("form.kssattr-formname-prenotazione_add").length){
      return;
    }

    let arr = $('input[name^="form.widgets.booking_type"]');
    let booking_type_cookie = getCookie(TIPOLOGIA_PRENOTAZIONE_COOKIE);

    if(!booking_type_cookie){
      return;
    }

    // sanitize type
    let preselcted_booking_type = booking_type_cookie.trim().slice(1, booking_type_cookie.length - 1)

    for(let i = 0; i < arr.length; i++){
      if(arr[i].value.includes(preselcted_booking_type)){
        $(arr[i]).prop('checked', true);
      }
    };

    document.cookie = TIPOLOGIA_PRENOTAZIONE_COOKIE +'=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';

  })
});
