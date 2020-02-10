/**
 * @file
 */

'use strict';

(function ($, Drupal) {
  const openText = Drupal.t("Expand all"),
        closeText = Drupal.t("Close all");

  Drupal.behaviors.avoindataExpanderBehavior = {
    attach: function (context) {
      $('.avoindata-expander', context).once('avoindataExpanderBehavior').each(function (index) {
        // Apply the avoindataExpanderBehavior effect to the elements only once.
        $('.avoindata-expander-header', this).on('click', toggleAvoindataExpander);

        // Add 'expand all' link above the first expander if there's more than one expander.
        if (index === 0 && $('.avoindata-expander').length > 1) {
          $('<div class="clearfix"><a id="toggle-all-avoindata-expanders-link" class="pull-right" data-expanded="false">' + openText + '</a></div>').insertBefore(this);
          $('#toggle-all-avoindata-expanders-link').on('click', toggleAllAvoindataExpanders);
        }

      });
    }
  };

  function toggleAvoindataExpander() {
    if ($(this.parentElement).hasClass('open') && !$(this).siblings().hasClass('collapsing')) {
      $('.avoindata-expander-content', this.parentElement).collapse('hide');
      $('.icon-wrapper i', this.parentElement).removeClass('fa-angle-up').addClass('fa-angle-down');
      $(this.parentElement).removeClass('open');
    }
    else if (!$(this.parentElement).hasClass('open') && !$(this).siblings().hasClass('collapsing')) {
      $('.avoindata-expander-content', this.parentElement).collapse('show');
      $('.icon-wrapper i', this.parentElement).removeClass('fa-angle-down').addClass('fa-angle-up');
      $(this.parentElement).addClass('open');
    }
    if (!$('.avoindata-expander').hasClass('open')) {
      $('#toggle-all-avoindata-expanders-link').data('expanded', true);
      toggleAllAvoindataExpanders();
    }
    if ($('.avoindata-expander').length > 0 && $('.avoindata-expander:not(.open)').length === 0) {
      $('#toggle-all-avoindata-expanders-link').data('expanded', false);
      toggleAllAvoindataExpanders();
    }
  }

  function toggleAllAvoindataExpanders() {
    if ($('#toggle-all-avoindata-expanders-link').data('expanded')) {
      $('.avoindata-expander-content').collapse('hide');
      $('.avoindata-expander').removeClass('open');
      $('.avoindata-expander .icon-wrapper > i').addClass('fa-angle-down').removeClass('fa-angle-up');
      $('#toggle-all-avoindata-expanders-link').data('expanded', false);
      $('#toggle-all-avoindata-expanders-link').text(openText);
    }
else {
      $('.avoindata-expander-content').collapse('show');
      $('.avoindata-expander').addClass('open');
      $('.avoindata-expander .icon-wrapper > i').removeClass('fa-angle-down').addClass('fa-angle-up');
      $('#toggle-all-avoindata-expanders-link').data('expanded', true);
      $('#toggle-all-avoindata-expanders-link').text(closeText);
    }

  }
})(jQuery, Drupal);
