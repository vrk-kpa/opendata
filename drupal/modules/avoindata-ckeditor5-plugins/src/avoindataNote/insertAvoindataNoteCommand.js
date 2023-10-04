/**
 * @file defines InsertAvoindataNoteCommand, which is executed when the avoindataNote
 * toolbar button is pressed.
 */

import { Command } from 'ckeditor5/src/core';

export default class InsertAvoindataNoteCommand extends Command {
  execute() {
    const { model } = this.editor;

    model.change((writer) => {
      // Insert <avoindataNote>*</avoindataNote> at the current selection position
      // in a way that will result in creating a valid model structure.
      model.insertContent(createAvoindataNote(writer));
    });
  }

  refresh() {
    const { model } = this.editor;
    const { selection } = model.document;

    // Determine if the cursor (selection) is in a position where adding a
    // avoindataNote is permitted. This is based on the schema of the model(s)
    // currently containing the cursor.
    const allowedIn = model.schema.findAllowedParent(
      selection.getFirstPosition(),
      'avoindataNote',
    );

    // If the cursor is not in a location where a avoindataNote can be added, return
    // null so the addition doesn't happen.
    this.isEnabled = allowedIn !== null;
  }
}

function createAvoindataNote(writer) {
  // Create instances of the elements registered with the editor in
  // avoindataexpanderediting.js.
  const avoindataNote = writer.createElement('avoindataNote');
  const avoindataNoteIcon = writer.createElement('avoindataNoteIcon');
  const avoindataNoteTitle = writer.createElement('avoindataNoteTitle');
  const avoindataNoteContent = writer.createElement('avoindataNoteContent');

  // Append the title and content elements to the avoindataNote, which matches
  // the parent/child relationship as defined in their schemas.
  writer.append(avoindataNoteIcon, avoindataNote);
  writer.append(avoindataNoteTitle, avoindataNote);
  writer.append(avoindataNoteContent, avoindataNote);

  // The text content will automatically be wrapped in a
  // `<p>`.
  writer.appendElement('paragraph', avoindataNoteTitle);
  writer.appendElement('paragraph', avoindataNoteContent);

  // Return the element to be added to the editor.
  return avoindataNote;
}
