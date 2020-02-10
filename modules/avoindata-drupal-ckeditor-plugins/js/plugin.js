/**
 * @file
 * Plugin to insert avoindata expander elements.
 */

(function () {
  // Register the plugin within the editor.
  CKEDITOR.plugins.add('avoindata_expander', {
    requires: 'widget',

    // Register the icons.
    icons: 'avoindata_expander',

    // The plugin initialization logic goes inside this method.
    init: function (editor) {
      editor.addContentsCss(this.path + '../css/style.css');

      // Allow any attributes.
      editor.config.allowedContent = true;
      CKEDITOR.dtd.$removeEmpty.i = 0;

      editor.widgets.add('avoindata_expander', {
        template:
          '<div class="avoindata-expander">' +
            '<div class="avoindata-expander-header">' +
              '<h2 class="avoindata-expander-title">Title</h2>' +
              '<span class="icon-wrapper pull-right"><i class="fas fa-angle-down"></i></span>' +
            '</div>' +
            '<div class="avoindata-expander-content collapse">Content</div>' +
          '</div>',

        editables: {
          title: {
              selector: '.avoindata-expander-title'
          },
          content: {
              selector: '.avoindata-expander-content'
          }
        },

        requiredContent: 'div(avoindata-expander) h2(avoindata-expander-title) div(avoindata-expander-content)',

        upcast: function (element) {
            return element.name == 'div' && element.hasClass('avoindata-expander');
        }
      });

      // Create a toolbar button that executes the above command.
      editor.ui.addButton('avoindata_expander', {
        // The command to execute on click.
        command: 'avoindata_expander',

        // The path to the icon.
        icon: this.path + '../icons/avoindata_expander.png'
      });
    }
  });

  // Register the plugin within the editor.
  CKEDITOR.plugins.add('avoindata_note', {
    requires: 'widget',

    // Register the icons.
    icons: 'avoindata_note',

    // The plugin initialization logic goes inside this method.
    init: function (editor) {
      editor.addContentsCss(this.path + '../css/style.css');

      // Allow any attributes.
      editor.config.allowedContent = true;
      CKEDITOR.dtd.$removeEmpty.i = 0;

      editor.widgets.add('avoindata_note', {
        template:
          '<div class="avoindata-note"><div class="avoindata-note-header">' +
              '<img class="avoindata-note-header-image" src="/resources/images/avoindata-note-icon.svg"/>' +
              '<h2 class="avoindata-note-title">Title</h2></div>' +
            '<div class="avoindata-note-content">Content</div></div>',

        editables: {
          title: {
              selector: '.avoindata-note-title'
          },
          content: {
              selector: '.avoindata-note-content'
          }
        },

        requiredContent: 'div(avoindata-note) h2(avoindata-note-title) div(avoindata-note-content)',

        upcast: function (element) {
            return element.name == 'div' && element.hasClass('avoindata-note');
        }
      });

      // Create a toolbar button that executes the above command.
      editor.ui.addButton('avoindata_note', {
        // The command to execute on click.
        command: 'avoindata_note',

        // The path to the icon.
        icon: this.path + '../icons/avoindata_note.png'
      });
    }
  });

  // Register the plugin within the editor.
  CKEDITOR.plugins.add('avoindata_hint', {
    requires: 'widget',

    // Register the icons.
    icons: 'avoindata_hint',

    // The plugin initialization logic goes inside this method.
    init: function (editor) {
      editor.addContentsCss(this.path + '../css/style.css');

      // Allow any attributes.
      editor.config.allowedContent = true;
      CKEDITOR.dtd.$removeEmpty.i = 0;

      editor.widgets.add('avoindata_hint', {
        template:
          '<div class="avoindata-hint">' +
            '<img class="avoindata-hint-image" src="/resources/images/avoindata-hint-icon.svg"/>' +
            '<div class="avoindata-hint-content">Content</div></div>',

        editables: {
          content: {
              selector: '.avoindata-hint-content'
          }
        },

        requiredContent: 'div(avoindata-hint) div(avoindata-hint-content)',

        upcast: function (element) {
            return element.name == 'div' && element.hasClass('avoindata-hint');
        }
      });

      // Create a toolbar button that executes the above command.
      editor.ui.addButton('avoindata_hint', {
        // The command to execute on click.
        command: 'avoindata_hint',

        // The path to the icon.
        icon: this.path + '../icons/avoindata_hint.png'
      });
    }
  });

  // Register the plugin within the editor.
  CKEDITOR.plugins.add('avoindata_example', {
    requires: 'widget',

    // Register the icons.
    icons: 'avoindata_example',

    // The plugin initialization logic goes inside this method.
    init: function (editor) {
      editor.addContentsCss(this.path + '../css/style.css');

      // Allow any attributes.
      editor.config.allowedContent = true;
      CKEDITOR.dtd.$removeEmpty.i = 0;

      editor.widgets.add('avoindata_example', {
        template:
          '<div class="avoindata-example"><div class="avoindata-example-header">' +
              '<h2 class="avoindata-example-title">Title</h2></div>' +
            '<div class="avoindata-example-content">Content</div></div>',

        editables: {
          title: {
              selector: '.avoindata-example-title'
          },
          content: {
              selector: '.avoindata-example-content'
          }
        },

        requiredContent: 'div(avoindata-example) h2(avoindata-example-title) div(avoindata-example-content)',

        upcast: function (element) {
            return element.name == 'div' && element.hasClass('avoindata-example');
        }
      });

      // Create a toolbar button that executes the above command.
      editor.ui.addButton('avoindata_example', {
        // The command to execute on click.
        command: 'avoindata_example',

        // The path to the icon.
        icon: this.path + '../icons/avoindata_example.png'
      });
    }
  });
})();
