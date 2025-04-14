/**
 * @file registers the avoindataExample toolbar button and binds functionality to it.
 */

import { Plugin } from 'ckeditor5/src/core';
import { ButtonView } from 'ckeditor5/src/ui';
import icon from '../../icons/icon-example.svg?source';

export default class AvoindataExampleUI extends Plugin {
  init() {
    const editor = this.editor;

    // This will register the avoindataExample toolbar button.
    editor.ui.componentFactory.add('avoindataExample', (locale) => {
      const command = editor.commands.get('insertAvoindataExampleCommand');
      const buttonView = new ButtonView(locale);

      // Create the toolbar button.
      buttonView.set({
        label: editor.t('Avoindata Example'),
        icon,
        tooltip: true,
      });

      buttonView.iconView.set({
        isColorInherited: false,
        viewBox: '0 0 24 24'
      })

      // Bind the state of the button to the command.
      buttonView.bind('isOn', 'isEnabled').to(command, 'value', 'isEnabled');

      // Execute the command when the button is clicked (executed).
      this.listenTo(buttonView, 'execute', () =>
        editor.execute('insertAvoindataExampleCommand'),
      );

      return buttonView;
    });
  }
}
