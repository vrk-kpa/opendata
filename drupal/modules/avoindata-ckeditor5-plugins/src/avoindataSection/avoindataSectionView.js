import {
  View,
  LabeledFieldView,
  createLabeledInputText,
  ButtonView,
  submitHandler,
  LabelView,
} from 'ckeditor5/src/ui';
import { icons } from 'ckeditor5/src/core';

export default class FormView extends View {
  constructor(locale) {
    super(locale);

    this.heading = new LabelView(this.locale);
    this.heading.setTemplate({
      tag: 'div',
      attributes: {
        class: ['title']
      },
      children: ['Avoindata section']
    })

    this.idInputView = this._createInput('Id');

    this.saveButtonView = this._createButton('Save', null, 'btn btn-primary');
    // Submit type of the button will trigger the submit event on entire form when clicked
    // (see submitHandler() in render() below).
    this.saveButtonView.type = 'submit';

    this.cancelButtonView = this._createButton('Cancel', null, 'btn btn-secondary');

    // Delegate ButtonView#execute to FormView#cancel
    this.cancelButtonView.delegate('execute').to(this, 'cancel');

    this.childViews = this.createCollection([
      this.heading,
      this.idInputView,
      this.saveButtonView,
      this.cancelButtonView
    ]);

    this.setTemplate({
      tag: 'form',
      attributes: {
        class: ['ck', 'ck-reset_all-excluded', 'avoindata-section-id-form'],
        tabindex: '-1'
      },
      children: this.childViews
    });
  }

  render() {
    super.render();

    // Submit the form when the user clicked the save button or pressed enter in the input.
    submitHandler({
      view: this
    });
  }

  focus() {
    this.childViews.get(1).focus();
  }

  _createInput(label) {
    const labeledInput = new LabeledFieldView(this.locale, createLabeledInputText);

    labeledInput.label = label;

    return labeledInput;
  }

  _createButton(label, icon, className) {
    const button = new ButtonView();

    button.set({
      label,
      icon,
      tooltip: true,
      class: className,
      withText: true,
    });

    return button;
  }
}
