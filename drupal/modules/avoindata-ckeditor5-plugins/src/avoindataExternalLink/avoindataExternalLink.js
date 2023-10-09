import { Plugin } from 'ckeditor5/src/core';
import '../../css/styles.css';

export default class AvoindataExternalLink extends Plugin {
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
  }

  static get pluginName() {
    return 'AvoindataExternalLink';
  }
}
