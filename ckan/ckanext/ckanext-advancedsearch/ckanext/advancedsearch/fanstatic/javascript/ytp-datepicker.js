// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
"use strict";

ckan.module("ytp-datepicker", function($) {
  return {
    initialize: function() {
      this.el.find("[data-datepicker]").each(function() {
        $(this)
          .datetimepicker({
            format: "YYYY-MM-DD",
            showClear: true
          })
      });
    }
  };
});
