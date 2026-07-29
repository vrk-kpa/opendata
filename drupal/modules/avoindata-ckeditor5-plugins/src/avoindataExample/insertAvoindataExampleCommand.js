/**
 * @file defines InsertAvoindataExampleCommand, which is executed when the avoindataExample
 * toolbar button is pressed.
 */

import { Command } from 'ckeditor5/src/core';

export default class InsertAvoindataExampleCommand extends Command {
  execute() {
    const { model } = this.editor;

    model.change((writer) => {
      // Insert <avoindataExample>*</avoindataExample> at the current selection position
      // in a way that will result in creating a valid model structure.
      const avoindataExample = createAvoindataExample(writer);
      model.insertContent(avoindataExample);
    });
  }

  refresh() {
    const { model } = this.editor;
    const { selection } = model.document;

    // Determine if the cursor (selection) is in a position where adding a
    // avoindataExample is permitted. This is based on the schema of the model(s)
    // currently containing the cursor.
    const allowedIn = model.schema.findAllowedParent(
      selection.getFirstPosition(),
      'avoindataExample',
    );

    // If the cursor is not in a location where a avoindataExample can be added, return
    // null so the addition doesn't happen.
    this.isEnabled = allowedIn !== null;
  }
}

function createAvoindataExample(writer) {
  // Create instances of the elements registered with the editor in
  // avoindataexpanderediting.js.
  const avoindataExample = writer.createElement('avoindataExample');
  const avoindataExampleTitle = writer.createElement('avoindataExampleTitle');
  const avoindataExampleContent = writer.createElement('avoindataExampleContent');

  // Append the title and content elements to the avoindataExample, which matches
  // the parent/child relationship as defined in their schemas.
  writer.append(avoindataExampleTitle, avoindataExample);
  writer.append(avoindataExampleContent, avoindataExample);

  // The text content will automatically be wrapped in a
  // `<p>`.
  const title = writer.createElement('paragraph');
  writer.insertText('Title', title, 0);
  writer.append(title, avoindataExampleTitle);
  const content = writer.createElement('paragraph');
  writer.insertText('Content', content, 0);
  writer.append(content, avoindataExampleContent);

  // Return the element to be added to the editor.
  return avoindataExample;
}
