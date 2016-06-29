(function($) {
  $(function() {

    // By default every panel is collapsed, so don't show "close all"
    $('.closeall').hide();

    // "Open all" button
    $('.openall').click(function(e){
      e.preventDefault();
      $('.panel-collapse:not(".in")').collapse('show');
      $('.closeall').show();
      $('.openall').hide();
    });

    // "Close all" button
    $('.closeall').click(function(e){
      e.preventDefault();
      $('.panel-collapse.in').collapse('hide');
      $('.openall').show();
      $('.closeall').hide();
    });

    // When any panel is opened or collapsed, check if buttons should be
    // shown or hidden
    $('[data-toggle="collapse"]').click(function(){
      isopen = $(this).attr('aria-expanded');

      // When a panel is closed, show "open all" and determine if "close all" 
      // should be hidden
      if (isopen === "true") {
        $('.openall').show();
        if ($('.panel-collapse.in').length <= 1) { // Number of open panels is checked before this panel actually closes
          $('.closeall').hide();
        }
      }
      // When a panel is opened, show "close all" and determine if "open all" 
      // should be hidden
      else {
        $('.closeall').show();
        if ($('.panel-collapse:not(".in")').length <= 1) { // Number of closed panels is checked before this panel actually opens
          $('.openall').hide();
        }
      }
    });

  });

})(jQuery);
