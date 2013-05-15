this.jQuery(function (jQuery) {
  jQuery('[data-toggle="ratings"]').on({
    click: function (event) {
      event.preventDefault();
      var toggle = jQuery(event.target);
      var target = jQuery(toggle.data('target'));

      if (target.is(':visible')) {
        target.hide();
        toggle.trigger('hidden');
      } else {
        target.show();
        toggle.trigger('shown');
      }
    },
    shown: function (event) {
      var link = jQuery(event.target);
      link.data('showText', link.text());
      link.text(link.data('hideText'));
    },
    hidden: function (event) {
      var link = jQuery(event.target);
      link.text(link.data('showText'));
    }
  });
});
