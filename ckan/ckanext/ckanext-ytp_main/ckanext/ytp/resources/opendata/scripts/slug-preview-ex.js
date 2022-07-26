this.ckan.module('slug-preview-target-ex', {
  initialize: function () {
    var sandbox = this.sandbox;
    var options = this.options;
    var el = this.el;

    // Make sure there isn't a value in the field already...
    if (el.val() == '') {
      // Once the preview box is modified stop watching it.
      sandbox.subscribe('slug-preview-ex-modified', function () {
        el.off('.slug-preview');
      });

      // Watch for updates to the target field and update the hidden slug field
      // triggering the "change" event manually.
      el.on('keyup.slug-preview input.slug-preview', function (event) {
        sandbox.publish('slug-target-ex-changed', this.value);
        //slug.val(this.value).trigger('change');
      });
    }
  }
});

this.ckan.module('slug-preview-slug-ex', function (jQuery) {
  return {
    options: {
      prefix: '',
      placeholder: '<slug>',
      label: 'URL',
    },

    initialize: function () {
      var sandbox = this.sandbox;
      var options = this.options;
      var el = this.el;
      var _ = sandbox.translate;

      var slug = el.slug();
      var parent = slug.parents('.form-group');
      var preview;

      if (!(parent.length)) {
        return;
      }

      // Leave the slug field visible
      if (!parent.hasClass('error')) {
        preview = parent.slugPreviewEx({
          prefix: options.prefix,
          placeholder: options.placeholder,
          i18n: {
            'URL': this._(options.label),
            'Edit': this._('Edit')
          }
        });

        // If the user manually enters text into the input we cancel the slug
        // listeners so that we don't clobber the slug when the title next changes.
        slug.keypress(function () {
          if (event.charCode) {
            sandbox.publish('slug-preview-ex-modified', preview[0]);
          }
        });

        sandbox.publish('slug-preview-ex-created', preview[0]);
      }

      // Watch for updates to the target field and update the hidden slug field
      // triggering the "change" event manually.
      sandbox.subscribe('slug-target-ex-changed', function (value) {
        slug.val(value).trigger('change');
      });
    }
  };
});

/* Creates a new preview element for a slug field that displays an example of
 * what the slug will look like. Also provides an edit button to toggle back
 * to the original form element.
 *
 * options - An object of plugin options (defaults to slugPreviewEx.defaults).
 *           prefix: An optional prefix to apply before the slug field.
 *           placeholder: Optional placeholder when there is no slug.
 *           i18n: Provide alternative translations for the plugin string.
 *           template: Provide alternative markup for the plugin.
 *
 * Examples
 *
 *   var previews = jQuery('[name=slug]').slugPreviewEx({
 *     prefix: 'example.com/resource/',
 *     placeholder: '<id>',
 *     i18n: {edit: 'éditer'}
 *   });
 *   // previews === preview objects.
 *   // previews.end() === [name=slug] objects.
 *
 * Returns the newly created collection of preview elements..
 */
(function ($, window) {
  var escape = $.url.escape;

  function slugPreviewEx(options) {
    options = $.extend(true, slugPreviewEx.defaults, options || {});

    var collected = this.map(function () {
      var element = $(this);
      var field = element.find('input');
      var preview = $(options.template);
      var value = preview.find('.slug-preview-value');
      var required = $('<div>').append($('.control-required', element).clone()).html();

      function setValue() {
        var val = escape(field.val()) || options.placeholder;
        value.text(val);
      }

      preview.find('.control-label').html(required + ' ' + options.i18n['URL']);
      preview.find('.slug-preview-prefix').text(options.prefix);
      preview.find('.edit-button').text(options.i18n['Edit']).click(function (event) {
        event.preventDefault();
        element.show();
        preview.hide();
      });

      setValue();
      field.on('change', setValue);

      element.after(preview).hide();

      return preview[0];
    });

    // Append the new elements to the current jQuery stack so that the caller
    // can modify the elements. Then restore the originals by calling .end().
    return this.pushStack(collected);
  }

  slugPreviewEx.defaults = {
    prefix: '',
    placeholder: '',
    i18n: {
      'URL': 'URL',
      'Edit': 'Edit'
    },
    template: [
      '<div class="slug-preview slug-preview--custom">',
      '<label class="control-label"></label>',
      '<div class="pt-2 pb-3"><span class="slug-preview-prefix"></span><span class="slug-preview-value"></span></div>',
      '<button class="btn btn-default btn-xs edit-button suomifi-button-secondary"></button>',
      '</div>'
    ].join('\n')
  };

  $.fn.slugPreviewEx = slugPreviewEx;

})(this.jQuery, this);
