/**
 * @file registers the avoindataSection toolbar button and binds functionality to it.
 */

import { Plugin } from 'ckeditor5/src/core';
import { ButtonView, ContextualBalloon, clickOutsideHandler } from 'ckeditor5/src/ui';
import FormView from './avoindataSectionView';
import icon from '../../icons/icon-section.svg?source';

export default class AvoindataSectionUI extends Plugin {
  static get requires() {
    return [ContextualBalloon];
  }

  init() {
    const editor = this.editor;
    // Create the balloon and the form view.
    this._balloon = editor.plugins.get(ContextualBalloon);
    this.formView = this._createFormView();
    const command = editor.commands.get('insertAvoindataSectionCommand');

    // This will register the avoindataSection toolbar button.
    editor.ui.componentFactory.add('avoindataSection', (locale) => {
      const buttonView = new ButtonView(locale);

      // Create the toolbar button.
      buttonView.set({
        label: editor.t('Avoindata Section widget'),
        icon,
        tooltip: true
      });

      // Bind the state of the button to the command.
      buttonView.bind('isOn', 'isEnabled').to(command, 'value', 'isEnabled');

      // Execute the command when the button is clicked (executed).
      /* this.listenTo(buttonView, 'execute', () =>
        editor.execute('insertAvoindataSectionCommand'),
      ); */

      // Show the UI on button click.
      this.listenTo(buttonView, 'execute', () => {
        this._showUI();
      });

      return buttonView;
    });
  }

  _createFormView() {
    const editor = this.editor;
    const formView = new FormView(editor.locale);

    // Execute the command after clicking the "Save" button.
    this.listenTo(formView, 'submit', () => {
      // Grab values from the input fields.
      const id = formView.idInputView.fieldView.element.value;

      editor.model.change(writer => {
        editor.execute('insertAvoindataSectionCommand', id);
      });

      // Hide the form view after submit.
      this._hideUI();
    });

    // Hide the form view after clicking the "Cancel" button.
    this.listenTo(formView, 'cancel', () => {
      this._hideUI();
    });

    // Hide the form view when clicking outside the balloon.
    clickOutsideHandler({
      emitter: formView,
      activator: () => this._balloon.visibleView === formView,
      contextElements: [this._balloon.view.element],
      callback: () => this._hideUI()
    });

    return formView;
  }

  _showUI() {
    const selection = this.editor.model.document.selection;

    this._balloon.add({
      view: this.formView,
      position: this._getBalloonPositionData()
    });

    const id = selection.getSelectedElement()?.getAttribute('avoindataSectionId') || '';
    this.formView.idInputView.fieldView.value = id;

    this.formView.focus();
  }

  _hideUI() {
    // Clear the input field values and reset the form.
    this.formView.idInputView.fieldView.value = '';
    this.formView.element.reset();

    this._balloon.remove(this.formView);

    // Focus the editing view after inserting the abbreviation so the user can start typing the content
    // right away and keep the editor focused.
    this.editor.editing.view.focus();
  }

  _getBalloonPositionData() {
    const view = this.editor.editing.view;
    const viewDocument = view.document;
    let target = null;

    // Set a target position by converting view selection range to DOM
    target = () => view.domConverter.viewRangeToDom(viewDocument.selection.getFirstRange());

    return {
      target
    };
  }
}
