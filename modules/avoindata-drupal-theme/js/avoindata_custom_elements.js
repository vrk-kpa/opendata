'use strict';

(function ($, Drupal) {
  const openText = Drupal.t("Expand all"),
        closeText = Drupal.t("Close all");

  Drupal.behaviors.avoindataExpanderBehavior = {
    attach: function (context) {
      $('.avoindata-expander', context).once('avoindataExpanderBehavior').each(function (index) {
        // Apply the avoindataExpanderBehavior effect to the elements only once.
        $(this).on('click', toggleAvoindataExpander);

        // Add 'expand all' link above the first expander if there's more than one expander
        if (index === 0 && $('.avoindata-expander').length > 1) {
          $('<div class="clearfix"><a id="toggle-all-avoindata-expanders-link" class="pull-right" data-expanded="false">' + openText + '</a></div>').insertBefore(this);
          $('#toggle-all-avoindata-expanders-link').on('click', toggleAllAvoindataExpanders);
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

  function toggleAllAvoindataExpanders() {
    if ($('#toggle-all-avoindata-expanders-link').data('expanded')) {
      $('.avoindata-expander-content').collapse('hide');
      $('.avoindata-expander').removeClass('open');
      $('.avoindata-expander .icon-wrapper > i').addClass('fa-angle-down').removeClass('fa-angle-up');
      $('#toggle-all-avoindata-expanders-link').data('expanded', false);
      $('#toggle-all-avoindata-expanders-link').text(openText);
    } else {
      $('.avoindata-expander-content').collapse('show');
      $('.avoindata-expander').addClass('open');
      $('.avoindata-expander .icon-wrapper > i').removeClass('fa-angle-down').addClass('fa-angle-up');
      $('#toggle-all-avoindata-expanders-link').data('expanded', true);
      $('#toggle-all-avoindata-expanders-link').text(closeText);
    }

  }
})(jQuery, Drupal);
