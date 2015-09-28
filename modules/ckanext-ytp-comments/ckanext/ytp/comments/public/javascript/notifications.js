this.ckan.module('notification', function($, _) {
	return {
		/* options object can be extended using data-module-* attributes */
		options : {
			action: null,
			loading: false,
            id: null,
			i18n: {
				follow: _('Subscribe'),
				unfollow: _('Unsubscribe')
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


            if (options.action == 'subscribe') {
                path = options.id + "/comments/subscription/add";
            } else {
                path = options.id + "/comments/subscription/remove";
            }

				this.el.addClass('disabled');

                $.ajax({
                    type: "POST",
                    url: path,
                    success: this._onClickLoaded,
                    error: function() {
                        console.log("Error!");
                    },
                    complete: function() {
                    }
                });

				//client.call('POST', path, { id : options.id }, this._onClickLoaded);
			}
		},

		_onClickLoaded: function(json) {
			var options = this.options;
			var sandbox = this.sandbox;
			options.loading = false;
			this.el.removeClass('disabled');

			if (options.action == 'subscribe') {
				options.action = 'unsubscribe';
				this.el.html('<i class="icon-remove-sign"></i> ' + this.i18n('Unsubscribe')).addClass('btn-danger');
			} else {
				options.action = 'subscribe';
				this.el.html('<i class="icon-plus-sign"></i> ' + this.i18n('Subscribe')).removeClass('btn-danger');
			}

            console.log("done");

            // what does this do?
			sandbox.publish('follow-' + options.action + '-' + options.id);
		}
	};
});
