/**
 * @file defines InsertAvoindataSectionCommand, which is executed when the avoindataSection
 * toolbar button is pressed.
 */

import { Command } from 'ckeditor5/src/core';

export default class InsertAvoindataSectionCommand extends Command {
  execute(id) {
    const { model } = this.editor;

    model.change((writer) => {
      const existingElement = writer.model.document.selection?.getSelectedElement();

      if (existingElement && existingElement.name == 'avoindataSection') {
        writer.setAttribute('avoindataSectionId', id, existingElement);
      } else {
        // Insert <avoindataSection>*</avoindataSection> at the current selection position
        // in a way that will result in creating a valid model structure.
        const avoindataSection = createAvoindataSection(writer, id);
        model.insertContent(avoindataSection);
        const selection = writer.createSelection(avoindataSection.getChild(0), 'in');
        writer.setSelection(selection)
      }
    });
  }

  refresh() {
    const { model } = this.editor;
    const { selection } = model.document;

    // Determine if the cursor (selection) is in a position where adding a
    // avoindataSection is permitted. This is based on the schema of the model(s)
    // currently containing the cursor.
    const allowedIn = model.schema.findAllowedParent(
      selection.getFirstPosition(),
      'avoindataSection',
    );

    // If the cursor is not in a location where a avoindataSection can be added, return
    // null so the addition doesn't happen.
    this.isEnabled = allowedIn !== null;
  }
}

function createAvoindataSection(writer, id) {
  // Create instances of the elements registered with the editor in avoindataexpanderediting.js.
  const avoindataSection = writer.createElement('avoindataSection', { avoindataSectionId: id });
  const avoindataSectionTitle = writer.createElement('avoindataSectionTitle');
  const avoindataSectionContent = writer.createElement('avoindataSectionContent');

  // Append the title and content elements to the avoindataSection, which matches
  // the parent/child relationship as defined in their schemas.
  writer.append(avoindataSectionTitle, avoindataSection);
  writer.append(avoindataSectionContent, avoindataSection);

  // The text content will automatically be wrapped in a
  // `<p>`.
  const title = writer.createElement('heading3');
  writer.insertText('Title', title, 0);
  writer.append(title, avoindataSectionTitle);
  const content = writer.createElement('paragraph');
  writer.insertText('Content', content, 0);
  writer.append(content, avoindataSectionContent);

  // Return the element to be added to the editor.
  return avoindataSection;
}
