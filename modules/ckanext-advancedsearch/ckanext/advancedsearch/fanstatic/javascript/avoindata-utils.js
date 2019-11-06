// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
'use strict';

ckan.module('avoindata-utils', function($) {
  return {
    initialize: function() {
      $.proxy(this, 'toggleCollapse');
        $('.more-options-link').on('click', (e) => this.toggleCollapse(e));
      $.proxy(this, 'submitForm');
        $('.avoindata-order-by').on('change', () => this.submitForm());
      $.proxy(this, 'submitEmptyForm');
      // Add 'clear all' link after the avoindata-pill if there's more than 4 avoindata-pills
      if ($('.avoindata-pill').length > 4 && $('#clear-all-link').length == 0) {
        $('<a id="clear-all-link" >' + this._("Clear all") + '</a>').insertAfter($('.avoindata-pill').last()).on('click', () => this.submitEmptyForm());
      }
    },
    toggleCollapse: function(e) {
      if (e.target.dataset.expanded === "true" && e.target.dataset.target && !$(e.target.dataset.target).hasClass('collapsing')) {
        e.target.dataset.expanded = "false";
        $(e.target.dataset.target).collapse('hide');
        $('span', e.target).text(this._("Show more options"));
        $('i', e.target).addClass('fa-angle-down').removeClass('fa-angle-up');
      } else if (e.currentTarget.dataset.expanded === "true" && e.currentTarget.dataset.target && !$(e.currentTarget.dataset.target).hasClass('collapsing')) {
        e.currentTarget.dataset.expanded = "false";
        $(e.currentTarget.dataset.target).collapse('hide');
        $('span', e.currentTarget).text(this._("Show more options"));
        $('i', e.currentTarget).addClass('fa-angle-down').removeClass('fa-angle-up');
      } else if (e.target.dataset.expanded === "false" && e.target.dataset.target && !$(e.target.dataset.target).hasClass('collapsing')) {
        e.target.dataset.expanded = "true";
        $(e.target.dataset.target).collapse('show');
        $('span', e.target).text(this._("Show less options"));
        $('i', e.target).removeClass('fa-angle-down').addClass('fa-angle-up');
      } else if (e.currentTarget.dataset.expanded === "false" && e.currentTarget.dataset.target && !$(e.currentTarget.dataset.target).hasClass('collapsing')) {
        e.currentTarget.dataset.expanded = "true";
        $(e.currentTarget.dataset.target).collapse('show');
        $('span', e.currentTarget).text(this._("Show less options"));
        $('i', e.currentTarget).removeClass('fa-angle-down').addClass('fa-angle-up');
      }
    },
    submitForm: function() {
      $('.advanced-search-form').submit();
    },
    submitEmptyForm: function() {
      if (confirm(this._("Are you sure you want to clear all filters?"))) {
        const form = document.createElement('form');
        form.method = 'post';
        document.body.appendChild(form);
        form.submit();
      }

    }
  }
});
