import { Plugin } from 'ckeditor5/src/core';

export default class ExternalLink extends Plugin {
  init() {
    const { conversion } = this.editor;

    // Upcast Converter for the old ckeditor4 plugin format
    conversion.for('upcast').elementToAttribute({
      model: 'linkIsExternal',
      view: {
        name: 'a',
        classes: ['external'],
        attributes: ['aria-label', 'target'],
      },
    });

    // Extra consumption for the leftover svg icon
    conversion.for('upcast').add(dispatcher => {
      // Look for every view svg element.
      dispatcher.on('element:svg', (evt, data, conversionApi) => {
        // Get all the necessary items from the conversion API object.
        const {
          consumable
        } = conversionApi;

        // Get view item from data object.
        const { viewItem } = data;

        // Define elements consumables.
        const svg = { name: 'svg', attributes: ['viewBox'] };
        const use = { name: 'use', attributes: ['href'] };

        // Tests if the view element can be consumed.
        if (!consumable.test(viewItem, svg)) {
          return;
        }

        // Check if there is only one child.
        if (viewItem.childCount !== 1) {
          return;
        }

        // Get the first child element.
        const firstChildItem = viewItem.getChild(0);

        // Check if the first element is a div.
        if (!firstChildItem.is('element', 'use')) {
          return;
        }

        // Tests if the first child element can be consumed.
        if (!consumable.test(firstChildItem, use)) {
          return;
        }

        // If a use tag inside a svg has the string 'avoindata_external-link' within the href
        // we can assume it's the old ckeditor4 plugin format and simply get rid of them
        if (firstChildItem?.getAttribute('href')?.includes('avoindata_external-link')) {
          // Consume the main outer wrapper element.
          consumable.consume(viewItem, svg);
          // Consume the inner wrapper element.
          consumable.consume(firstChildItem, use);
        }
      });
    });
    /*
    const editor = this.editor;

    // `listenTo()` and `editor` are available thanks to `Plugin`.
    // By using `listenTo()` you will ensure that the listener is removed when
    // the plugin is destroyed.
    this.listenTo(editor.data, 'ready', () => {
      const linkCommand = editor.commands.get('link');
      const { selection } = editor.model.document;

      let linkCommandExecuting = false;

      linkCommand.on('execute', (evt, args) => {
        const linkIsExternal = args[1]['linkIsExternal']

        if (linkIsExternal) {
          if (linkCommandExecuting) {
            linkCommandExecuting = false;
            return;
          }

          // If the additional attribute was passed, we stop the default execution
          // of the LinkCommand. We're going to create Model#change() block for undo
          // and execute the LinkCommand together with setting the extra attribute.
          evt.stop();

          // Prevent infinite recursion by keeping records of when link command is
          // being executed by this function.
          linkCommandExecuting = true;

          // Wrapping the original command execution in a model.change() block to make sure there's a single undo step
          // when the extra attribute is added.

          editor.model.change(writer => {
            editor.execute('link', ...args);
            const link = selection.getLastPosition().nodeBefore;
            // writer.insertElement('avoindataExternalLink', selection.getLastPosition())
          });
        }
      })
    });
    */
  }

  static get pluginName() {
    return 'ExternalLink';
  }
}
