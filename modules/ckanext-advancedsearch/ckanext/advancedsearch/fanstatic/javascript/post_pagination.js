'use strict';

ckan.module('post-pagination', function($) {
  return {
    initialize: function() {
        $.proxy(this, 'handlePaginationClick');
        // Get the actual dom element and not the JQuery version for event propagation
        document
            .querySelector('.pagination')
            .addEventListener('click', (e) => this.handlePaginationClick(e), true)
    },
    handlePaginationClick: function(e) {
        if (!e.target.value) {
            throw new Error('POST Pagination value empty')
        }
        this.post(this.options.prevQuery, e.target.value)
    },
    post: function(params, page_num) {
        const form = document.createElement('form');
        form.method = 'post';

        params.page = page_num

        const newNormalField = (key, value) => {
            const hiddenField = document.createElement('input');
            hiddenField.type = 'hidden';
            hiddenField.name = key;
            hiddenField.value = value;

            form.appendChild(hiddenField);
        }

        const newCheckBoxField = (key, values) => {
            for (let value of values) {
                const hiddenField = document.createElement('input');
                hiddenField.type = 'hidden';
                hiddenField.name = key;
                hiddenField.value = value;
                form.appendChild(hiddenField)
            }
        }

        for (const key in params) {
            if (params.hasOwnProperty(key)) {
                if (params[key].length > 1) {
                    newCheckBoxField(key, params[key])
                } else {
                    newNormalField(key, params[key])
                }
            }
        }
    
        document.body.appendChild(form);
        form.submit();
    }
  }
});
