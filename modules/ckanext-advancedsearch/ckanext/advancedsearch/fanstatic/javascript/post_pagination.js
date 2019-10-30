'use strict';

ckan.module('post-pagination', function($) {
  return {
    initialize: function() {
        $.proxy(this, 'handlePaginationClick');
        // Get the actual dom element and not the JQuery version for event propagation
        // Event is attached to parent container.
        // The click events on children propagate and trigger the event on the parent.
        document
            .querySelector('.pagination')
            .addEventListener('click', (e) => this.handlePaginationClick(e), true)
    },
    handlePaginationClick: function(e) {
        if (!e.target.value) {
            // Throw error for sentry.io tracking
            throw new Error('POST Pagination value empty')
        }
        e.preventDefault();
        e.stopPropagation();
        this.post(this.options.prevQuery, e.target.value)

    },
    post: function(params, page_num) {
        const form = document.createElement('form');
        form.method = 'post';

        params.page = page_num

        const newField = (key, value) => {
            const hiddenField = document.createElement('input');
            hiddenField.type = 'hidden';
            hiddenField.name = key;
            hiddenField.value = value;

            form.appendChild(hiddenField);
        }

        for (const key in params) {
            if (params.hasOwnProperty(key)) {
                if (Array.isArray(params[key]) && params[key].length > 1) {
                    // Checkbox fields contain multiple values for a single key
                    for (let value of params[key]) {
                        newField(key, value)
                    }
                } else {
                    newField(key, params[key])
                }
            }
        }

        document.body.appendChild(form);
        form.submit();
    }
  }
});
