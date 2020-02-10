'use strict';

ckan.module('clear-filter', function($) {
  return {
    initialize: function() {
      $.proxyAll(this, 'handleClearFilterClick');
      $('.avoindata-pill').on('click', e => this.handleClearFilterClick(e));
    },
    handleClearFilterClick: function(e) {
      if (e.currentTarget.dataset.key && e.currentTarget.dataset.value) {
        var key = e.currentTarget.dataset.key;
        var value = e.currentTarget.dataset.value;
        e.preventDefault();
        e.stopPropagation();
        this.post(e.currentTarget.dataset.query, key, value);
      }
    },
    post: function(params, k, v) {
      const form = document.createElement('form');
      form.method = 'post';

      const newField = (key, value) => {
        const hiddenField = document.createElement('input');
        hiddenField.type = 'hidden';
        hiddenField.name = key;
        hiddenField.value = value;

        form.appendChild(hiddenField);
      };

      var obj = JSON.parse(params);
      for (const key in obj) {
        if (key == k && v == 'all') {
          continue;
        } else {
          if (obj.hasOwnProperty(key)) {
            if (Array.isArray(obj[key]) && obj[key].length > 0) {
              for (let value of obj[key]) {
                if (key != k || value != v) {
                  newField(key, value);
                }
              }
            }
          }
        }
      }

      document.body.appendChild(form);
      form.submit();
    }
  };
});
