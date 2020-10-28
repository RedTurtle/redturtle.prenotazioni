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
});
