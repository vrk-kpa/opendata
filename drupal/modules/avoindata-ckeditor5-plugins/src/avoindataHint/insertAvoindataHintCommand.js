/**
 * @file defines InsertAvoindataHintCommand, which is executed when the avoindataHint
 * toolbar button is pressed.
 */

import { Command } from 'ckeditor5/src/core';

export default class InsertAvoindataHintCommand extends Command {
  execute() {
    const { model } = this.editor;

    model.change((writer) => {
      // Insert <avoindataHint>*</avoindataHint> at the current selection position
      // in a way that will result in creating a valid model structure.
      model.insertContent(createAvoindataHint(writer));
    });
  }

  refresh() {
    const { model } = this.editor;
    const { selection } = model.document;

    // Determine if the cursor (selection) is in a position where adding a
    // avoindataHint is permitted. This is based on the schema of the model(s)
    // currently containing the cursor.
    const allowedIn = model.schema.findAllowedParent(
      selection.getFirstPosition(),
      'avoindataHint',
    );

    // If the cursor is not in a location where a avoindataHint can be added, return
    // null so the addition doesn't happen.
    this.isEnabled = allowedIn !== null;
  }
}

function createAvoindataHint(writer) {
  // Create instances of the elements registered with the editor in
  // avoindataexpanderediting.js.
  const avoindataHint = writer.createElement('avoindataHint');
  const avoindataHintIcon = writer.createElement('avoindataHintIcon');
  const avoindataHintContent = writer.createElement('avoindataHintContent');

  // Append the title and content elements to the avoindataHint, which matches
  // the parent/child relationship as defined in their schemas.
  writer.append(avoindataHintIcon, avoindataHint);
  writer.append(avoindataHintContent, avoindataHint);

  // The text content will automatically be wrapped in a
  // `<p>`.
  writer.appendElement('paragraph', avoindataHintContent);

  // Return the element to be added to the editor.
  return avoindataHint;
}
