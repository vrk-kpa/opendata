/**
 * @file
 * Plugin to insert avoindata expander elements.
 *
 */

(function () {
  // Register the plugin within the editor.
  CKEDITOR.plugins.add('avoindata_expander', {
    requires: 'widget',

    // Register the icons.
    icons: 'avoindata_expander',

    // The plugin initialization logic goes inside this method.
    init: function (editor) {
      editor.addContentsCss( this.path + '../css/style.css' );

      // Allow any attributes.
      editor.config.allowedContent = true;
      CKEDITOR.dtd.$removeEmpty.i = 0;


      editor.widgets.add( 'avoindata_expander', {
        template:
          '<div class="avoindata-expander" onclick="toggleAvoindataExpander(this)">' +
            '<div class="avoindata-expander-header">' +
              '<h2 class="avoindata-expander-title">Title</h2>' +
              '<span class="icon-wrapper pull-right"><i class="fas fa-angle-down"></i></span>' +
            '</div>' +
            '<div class="avoindata-expander-content collapse"><p>Content...</p></div>' +
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

        upcast: function( element ) {
            return element.name == 'div' && element.hasClass( 'avoindata-expander' );
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
})();
