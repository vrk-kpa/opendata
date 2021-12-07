'use strict';

ckan.module('bulk-confirm-action', function(jQuery) {
  return {
    options: {
      content: '',
      template: `
        <div class="modal fade">
          <div class="modal-dialog">
            <div class="modal-content">
              <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal">×</button>
                <h3 class="modal-title"></h3>
              </div>
              <div class="modal-body">
              </div>
              <div class="modal-footer">
                <button class="btn btn-default btn-cancel"></button>
                <button class="btn btn-primary"></button>
              </div>
            </div>
          </div>
        </div>
      `,
    },
    // This will be true when event has been confirmed, allows/prevents default button execution
    confirmed_action: false,

    initialize: function() {
      jQuery.proxyAll(this, /_on/);
      jQuery.proxyAll(this, 'performAction');
      this.el.on('click', this._onClick);
    },

    /* Presents the user with a confirm dialogue to ensure that they wish to
     * continue with the current action.
     *
     * Examples
     *
     *   jQuery('.delete').click(function () {
     *     module.confirm();
     *   });
     *
     * Returns nothing.
     */
    confirm: function() {
      this.sandbox.body.append(this.createModal());
      this.modal.modal('show');

      // Center the modal in the middle of the screen.
      this.modal.css({
        'margin-top': this.modal.height() * -0.5,
        top: '50%',
      });
    },

    /* Creates the modal dialog, attaches event listeners and localised
     * strings.
     *
     * Returns the newly created element.
     */
    createModal: function() {
      if (!this.modal) {
        var element = (this.modal = jQuery(this.options.template));
        element.on('click', '.btn-primary', this._onConfirmSuccess);
        element.on('click', '.btn-cancel', this._onConfirmCancel);
        element.modal({ show: false });

        element.find('.modal-title').text(this._('Please Confirm Action'));
        var content =
          this.options.content ||
          this.options.i18n.content /* Backwards-compatibility */ ||
          this._('Are you sure you want to perform this action?');
        element.find('.modal-body').text(content);
        element.find('.btn-primary').text(this._('Confirm'));
        element.find('.btn-cancel').text(this._('Cancel'));
      }
      return this.modal;
    },

    /* Event handler that displays the confirm dialog */
    _onClick: function(event) {
        // If event has been confirmed let the click event finish else preventDefault
        // NOTE: click event is retriggered on confirmation
        if (this.confirmed_action) {
            this.confirmed_action = false
            return;
        }

        event.preventDefault();
        this.confirm();
    },

    /* Event handler for the success event */
    _onConfirmSuccess: function(event) {
        this.confirmed_action = true
        this.el.trigger('click');
        this.modal.modal('hide');
    },

    /* Event handler for the cancel event */
    _onConfirmCancel: function(event) {
      this.modal.modal('hide');
    },
  };
});
