/**
 * @file registers the avoindataExpander toolbar button and binds functionality to it.
 */

import { Plugin } from 'ckeditor5/src/core';
import { ButtonView } from 'ckeditor5/src/ui';
import icon from '../../icons/icon-expander.svg?source';

export default class AvoindataExpanderUI extends Plugin {
  init() {
    const editor = this.editor;

    // This will register the avoindataExpander toolbar button.
    editor.ui.componentFactory.add('avoindataExpander', (locale) => {
      const command = editor.commands.get('insertAvoindataExpanderCommand');
      const buttonView = new ButtonView(locale);

      // Create the toolbar button.
      buttonView.set({
        label: editor.t('Avoindata Expander'),
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
        editor.execute('insertAvoindataExpanderCommand'),
      );

      return buttonView;
    });
  }
}
