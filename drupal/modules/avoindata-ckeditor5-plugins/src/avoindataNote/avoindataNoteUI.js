/**
 * @file registers the avoindataNote toolbar button and binds functionality to it.
 */

import { Plugin } from 'ckeditor5/src/core';
import { ButtonView } from 'ckeditor5/src/ui';
import icon from '../../icons/icon-info.svg?source';

export default class AvoindataNoteUI extends Plugin {
  init() {
    const editor = this.editor;

    // This will register the avoindataNote toolbar button.
    editor.ui.componentFactory.add('avoindataNote', (locale) => {
      const command = editor.commands.get('insertAvoindataNoteCommand');
      const buttonView = new ButtonView(locale);

      // Create the toolbar button.
      buttonView.set({
        label: editor.t('Avoindata Note'),
        icon,
        tooltip: true,
      });

      // Bind the state of the button to the command.
      buttonView.bind('isOn', 'isEnabled').to(command, 'value', 'isEnabled');

      // Execute the command when the button is clicked (executed).
      this.listenTo(buttonView, 'execute', () =>
        editor.execute('insertAvoindataNoteCommand'),
      );

      return buttonView;
    });
  }
}
