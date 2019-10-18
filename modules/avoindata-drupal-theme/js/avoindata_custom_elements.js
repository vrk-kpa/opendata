'use strict';

(function ($, Drupal) {
  Drupal.behaviors.avoindataExpanderBehavior = {
    attach: function (context) {
      $('.avoindata-expander', context).once('avoindataExpanderBehavior').each(function (index) {
        // Apply the avoindataExpanderBehavior effect to the elements only once.
        $(this).on('click', toggleAvoindataExpander);

        // Add 'expand all' link above the first expander if there's more than one expander
        if (index === 0 && $('.avoindata-expander').length > 1) {
          $('<div class="clearfix"><a id="open-all-avoindata-expanders-link" class="pull-right">' + Drupal.t("Expand all") + '</a></div>').insertBefore(this);
          $('#open-all-avoindata-expanders-link').on('click', openAllAvoindataExpanders);
        }

      });
    }
  };

  function toggleAvoindataExpander() {
    $('.avoindata-expander-content', this).collapse('toggle');
    const iconEl = $('.icon-wrapper i', this);
    iconEl.hasClass('fa-angle-down') ? iconEl.removeClass('fa-angle-down').addClass('fa-angle-up') : iconEl.removeClass('fa-angle-up').addClass('fa-angle-down')
    $(this).toggleClass('open');
  }

  function openAllAvoindataExpanders() {
    $('.avoindata-expander-content').collapse('show');
    $('.avoindata-expander').addClass('open');
    $('.avoindata-expander .icon-wrapper > i').removeClass('fa-angle-down').addClass('fa-angle-up');
  }
})(jQuery, Drupal);
