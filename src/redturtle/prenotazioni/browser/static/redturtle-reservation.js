/*globals jQuery, document, rgprenotazioni*/
/*jslint sloppy: true, vars: true, white: true, maxerr: 50, indent: 4 */
/*
 * This is the javascript that looks for overlays
 */
(function (jQuery) {
    /*
    * Apply an overlay to all the links with class infoIco like
    */
    // function prepOverlay() {
    //     return jQuery('a.prenotazioni-popup').prepOverlay({
    //         subtype: 'ajax'
    //     });
    // }
    // jQuery(document).ready(prepOverlay);
}(jQuery));

(function (jQuery) {
    /*
     * Apply the dateinput widget to elements with class rg-dateinput
     */
    function rgdateinput() {
        if (!jQuery.fn.dateinput) {
            return false;
        }

        function sync_inputs(backend, frontend) {
            backend.val(frontend.getValue('yyyy-mm-dd'));
        }

        jQuery('.rg-dateinput').each(
            function(idx, el) {
                var frontend = jQuery(el).removeClass('rg-dateinput');
                var backend = frontend.clone().attr({type: 'hidden'});
                jQuery('label[for="' + backend.attr('name') + '"] .formHelp').remove();
                frontend.after(backend);
                frontend.dateinput(
                    {
                        change: function() {
                            sync_inputs(backend, this);
                        }
                    }
                );
                frontend.removeClass('date');
                frontend.attr({name: backend.attr('name') + Math.random()});
            }
        );
    }
    jQuery(document).ready(rgdateinput);
}(jQuery));
