this.ckan.module('notification', function($, _) {
    return {
        /* options object can be extended using data-module-* attributes */
        options : {
            action: null,
            loading: false,
            id: null,
            i18n: {
                subscribe: _('Subscribe to comments'),
                unsubscribe: _('Unsubscribe from comments')
            }
        },

        initialize: function () {
            $.proxyAll(this, /_on/);
            this.el.on('click', this._onClick);
        },

        _onClick: function(event) {
            var options = this.options;
            if (
                options.action
                && options.id
                && !options.loading
            ) {
                event.preventDefault();
                var client = this.sandbox.client;
                options.loading = true;


            // depending on the data-module-id variable, either subscribe or unsubscribe
            if (options.action == 'subscribe') {
                path = options.id + "/subscription/add";
            } else {
                path = options.id + "/subscription/remove";
            }
                this.el.addClass('disabled');

                console.log(path);

                $.ajax({
                    type: "POST",
                    url: path,
                    success: this._onClickLoaded,
                    error: function() {
                        console.log("Subscribing to comment notifications failed.");
                    }
                });

            }
        },

        _onClickLoaded: function(json) {
            var options = this.options;
            var sandbox = this.sandbox;
            options.loading = false;
            this.el.removeClass('disabled');

            if (options.action == 'subscribe') {
                options.action = 'unsubscribe';
                this.el.html('<i class="icon-remove-sign"></i> ' + this.i18n('unsubscribe')).addClass('btn-danger');
            } else {
                options.action = 'subscribe';
                this.el.html('<i class="icon-plus-sign"></i> ' + this.i18n('subscribe')).removeClass('btn-danger');
            }

            console.log("done");

            sandbox.publish('notification-' + options.action + '-' + options.id);
        }
    };
});
