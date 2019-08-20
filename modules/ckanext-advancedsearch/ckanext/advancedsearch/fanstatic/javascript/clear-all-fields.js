// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
'use strict';

ckan.module('clear-all-fields', function($) {
  return {
    initialize: function() {
        $.proxyAll(this, /_/);
        this.el.on('click', this._clear);
    },
    _clear: function(e) {
        e.preventDefault();
        $('input').each((i, item) => {
            this._handleInputs(item)
        });
    },
    _handleInputs: function(elem) {
        switch(elem.type) {
            case 'text':
            case 'search':
            case 'datetime-local':
            case 'email':
            case 'hidden':
            case 'month':
            case 'number':
            case 'password':
            case 'tel':
            case 'time':
            case 'url':
            case 'week':
            case 'date':
                elem.value = ""
                break;
            case 'checkbox':
                elem.checked = false
                // The onchange event can be attached to the parent element
                // Event propagation "bubbles" triggers the event in the parent
                elem.dispatchEvent(new Event('change', { bubbles: true }))
                break;
            default:
                break;
        }
    }
  }
});
