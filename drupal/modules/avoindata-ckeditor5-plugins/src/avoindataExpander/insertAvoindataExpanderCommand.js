/**
 * @file defines InsertAvoindataExpanderCommand, which is executed when the avoindataExpander
 * toolbar button is pressed.
 */

import { Command } from 'ckeditor5/src/core';

export default class InsertAvoindataExpanderCommand extends Command {
  execute() {
    const { model } = this.editor;

    model.change((writer) => {
      // Insert <avoindataExpander>*</avoindataExpander> at the current selection position
      // in a way that will result in creating a valid model structure.
      const avoindataExpander = createAvoindataExpander(writer);
      model.insertContent(avoindataExpander);
    });
  }

  refresh() {
    const { model } = this.editor;
    const { selection } = model.document;

    // Determine if the cursor (selection) is in a position where adding a
    // avoindataExpander is permitted. This is based on the schema of the model(s)
    // currently containing the cursor.
    const allowedIn = model.schema.findAllowedParent(
      selection.getFirstPosition(),
      'avoindataExpander',
    );

    // If the cursor is not in a location where a avoindataExpander can be added, return
    // null so the addition doesn't happen.
    this.isEnabled = allowedIn !== null;
  }
}

function createAvoindataExpander(writer) {
  // Create instances of the three elements registered with the editor in
  // avoindataexpanderediting.js.
  const avoindataExpander = writer.createElement('avoindataExpander');
  const avoindataExpanderTitle = writer.createElement('avoindataExpanderTitle');
  const avoindataExpanderContent = writer.createElement('avoindataExpanderContent');

  // Append the title and content elements to the avoindataExpander, which matches
  // the parent/child relationship as defined in their schemas.
  writer.append(avoindataExpanderTitle, avoindataExpander);
  writer.append(avoindataExpanderContent, avoindataExpander);

  // The text content will automatically be wrapped in a
  // `<p>`.
  const title = writer.createElement('paragraph');
  writer.insertText('Title', title, 0);
  writer.append(title, avoindataExpanderTitle);
  const content = writer.createElement('paragraph');
  writer.insertText('Content', content, 0);
  writer.append(content, avoindataExpanderContent);

  // Return the element to be added to the editor.
  return avoindataExpander;
}
