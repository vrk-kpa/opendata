/**
 * @file registers the avoindataHint toolbar button and binds functionality to it.
 */

import { Plugin } from 'ckeditor5/src/core';
import { ButtonView } from 'ckeditor5/src/ui';
import icon from '../../icons/icon-hint.svg?source';

export default class AvoindataHintUI extends Plugin {
  init() {
    const editor = this.editor;

    // This will register the avoindataHint toolbar button.
    editor.ui.componentFactory.add('avoindataHint', (locale) => {
      const command = editor.commands.get('insertAvoindataHintCommand');
      const buttonView = new ButtonView(locale);

      // Create the toolbar button.
      buttonView.set({
        label: editor.t('Avoindata Hint'),
        icon,
        tooltip: true,
      });

      // Bind the state of the button to the command.
      buttonView.bind('isOn', 'isEnabled').to(command, 'value', 'isEnabled');

      // Execute the command when the button is clicked (executed).
      this.listenTo(buttonView, 'execute', () =>
        editor.execute('insertAvoindataHintCommand'),
      );

      return buttonView;
    });
  }
}
