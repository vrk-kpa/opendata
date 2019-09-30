'use strict';

// TODO: how to make this work with localization?
window.onload = function() {
  jQuery('<div class="clearfix"><a id="open-all-avoindata-expanders-link" class="pull-right" onclick="openAllAvoindataExpanders()">Avaa kaikki</a></div>').insertBefore('.avoindata-expander:first')
};

function toggleAvoindataExpander(e) {
  jQuery(e).children('.avoindata-expander-content').collapse('toggle');
  const iconEl = jQuery(e).children('.avoindata-expander-header').children('.icon-wrapper').children('i');
  iconEl.hasClass('fa-angle-down') ? iconEl.removeClass('fa-angle-down').addClass('fa-angle-up') : iconEl.removeClass('fa-angle-up').addClass('fa-angle-down')
  jQuery(e).toggleClass('open');
}

function openAllAvoindataExpanders() {
  jQuery('.avoindata-expander-content').collapse('show');
  jQuery('.avoindata-expander').addClass('open');
  jQuery('.avoindata-expander .icon-wrapper > i').removeClass('fa-angle-down').addClass('fa-angle-up');
}