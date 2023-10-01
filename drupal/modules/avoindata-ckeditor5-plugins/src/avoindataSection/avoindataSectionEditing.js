import { Plugin } from 'ckeditor5/src/core';
import { toWidget, toWidgetEditable } from 'ckeditor5/src/widget';
import { Widget } from 'ckeditor5/src/widget';
import InsertAvoindataSectionCommand from './insertAvoindataSectionCommand';

/**
 * CKEditor 5 plugins do not work directly with the DOM. They are defined as
 * plugin-specific data models that are then converted to markup that
 * is inserted in the DOM.
 *
 * CKEditor 5 internally interacts with section as this model:
 * <avoindataSection avoindataSectionId="">
 *     <avoindataSectionTitle></avoindataSectionTitle>
 *     <avoindataSectionContent></avoindataSectionContent>
 * </avoindataSection>
 *
 * Which is converted for the browser/user as this markup
 * <div class="avoindata-section" id="">
 *    <div class="avoindata-section-title">Title</div>
 *   <div class="avoindata-section-content">Content</div>
 * </div>
 *
 * This file has the logic for defining the avoindataSection model, and for how it is
 * converted to standard DOM markup.
 */
export default class AvoindataSectionEditing extends Plugin {
  static get requires() {
    return [Widget];
  }

  init() {
    this._defineSchema();
    this._defineConverters();
    this.editor.commands.add(
      'insertAvoindataSectionCommand',
      new InsertAvoindataSectionCommand(this.editor),
    );
  }

  /*
   * This registers the structure that will be seen by CKEditor 5 as
   * <avoindataSection avoindataSectionId="">
   *     <avoindataSectionTitle></avoindataSectionTitle>
   *     <avoindataSectionContent></avoindataSectionContent>
   * </avoindataSection>
   *
   * The logic in _defineConverters() will determine how this is converted to
   * markup.
   */
  _defineSchema() {
    // Schemas are registered via the central `editor` object.
    const schema = this.editor.model.schema;

    schema.register('avoindataSection', {
      // Behaves like a self-contained object (e.g. an image).
      isObject: true,
      // Allow in places where other blocks are allowed (e.g. directly in the root).
      allowWhere: '$block',
      allowAttributes: ['avoindataSectionId']
    });

    schema.register('avoindataSectionTitle', {
      // This creates a boundary for external actions such as clicking and
      // and keypress. For section, when the cursor is inside this box, the
      // keyboard shortcut for "select all" will be limited to the contents of
      // the box.
      isLimit: true,
      // This is only to be used within avoindataSection.
      allowIn: 'avoindataSection',
      // Allow content that is allowed in blocks (e.g. text with attributes).
      allowContentOf: '$root',
    });

    schema.register('avoindataSectionContent', {
      isLimit: true,
      allowIn: 'avoindataSection',
      allowContentOf: '$root',
    });

    schema.addChildCheck((context, childDefinition) => {
      // Disallow avoindataSection inside avoindataSectionContent.
      if (
        (context.endsWith('avoindataSectionContent') || context.endsWith('avoindataSectionTitle')) &&
        childDefinition.name === 'avoindataSection'
      ) {
        return false;
      }
    });
  }

  /**
   * Converters determine how CKEditor 5 models are converted into markup and
   * vice-versa.
   */
  _defineConverters() {
    // Converters are registered via the central editor object.
    const { conversion } = this.editor;

    // Upcast Converters: determine how existing HTML is interpreted by the
    // editor. These trigger when an editor instance loads.
    //
    // If <div class="avoindata-section"> is present in the existing markup
    // processed by CKEditor, then CKEditor recognizes and loads it as a
    // <avoindataSection> model.
    conversion.for('upcast').elementToElement({
      model: (viewElement, { writer }) => {
        return writer.createElement('avoindataSection', { avoindataSectionId: viewElement.getAttribute('id') });
      },
      view: {
        name: 'div',
        classes: 'avoindata-section',
        attributes: ['id']
      },
    });

    // If <div class="avoindata-section-title"> is present in the existing markup
    // processed by CKEditor, then CKEditor recognizes and loads it as a
    // <avoindataSectionTitle> model, provided it is a child element of <avoindataSection>,
    // as required by the schema.
    conversion.for('upcast').elementToElement({
      model: 'avoindataSectionTitle',
      view: {
        name: 'div',
        classes: 'avoindata-section-title',
      },
    });

    // If <div class="avoindata-section-content"> is present in the existing markup
    // processed by CKEditor, then CKEditor recognizes and loads it as a
    // <avoindataSectionContent> model, provided it is a child element of
    // <avoindataSection>, as required by the schema.
    conversion.for('upcast').elementToElement({
      model: 'avoindataSectionContent',
      view: {
        name: 'div',
        classes: 'avoindata-section-content',
      },
    });

    // Data Downcast Converters: converts stored model data into HTML.
    // These trigger when content is saved.

    // Instances of <avoindataSection> are saved as
    // <div class="avoindata-section">{{inner content}}</div>.
    conversion.for('dataDowncast').elementToElement({
      model: {
        name: 'avoindataSection',
        attributes: ['avoindataSectionId']
      },
      view: (modelElement, { writer }) => {
        return writer.createContainerElement(
          'div', { class: 'avoindata-section', id: modelElement.getAttribute('avoindataSectionId') }
        );
      }
    });

    // Instances of <avoindataSectionTitle> are saved as
    // <div class="avoindata-section-title">{{inner content}}</div>.
    conversion.for('dataDowncast').elementToElement({
      model: 'avoindataSectionTitle',
      view: {
        name: 'div',
        classes: 'avoindata-section-title',
      },
    });

    // Instances of <avoindataSectionContent> are saved as
    // <div class="savoindata-section-content" id="">{{inner content}}</div>.
    conversion.for('dataDowncast').elementToElement({
      model: 'avoindataSectionContent',
      view: {
        name: 'div',
        classes: 'avoindata-section-content',
      },
    });

    // Editing Downcast Converters. These render the content to the user for
    // editing, i.e. this determines what gets seen in the editor. These trigger
    // after the Data Upcast Converters, and are re-triggered any time there
    // are changes to any of the models' properties.
    //
    // Convert the <avoindataSection> model into a container widget in the editor UI.
    conversion.for('editingDowncast').elementToElement({
      model: {
        name: 'avoindataSection',
        attributes: ['avoindataSectionId']
      },
      view: (modelElement, { writer: viewWriter }) => {
        const section = viewWriter.createContainerElement('div', {
          class: 'avoindata-section',
          id: modelElement.getAttribute('avoindataSectionId')
        });

        return toWidget(section, viewWriter, { label: 'Avoindata Section widget' });
      },
    });

    // Convert the <avoindataSectionTitle> model into an editable <div> widget.
    conversion.for('editingDowncast').elementToElement({
      model: 'avoindataSectionTitle',
      view: (modelElement, { writer: viewWriter }) => {
        const div = viewWriter.createEditableElement('div', {
          class: 'avoindata-section-title',
        });
        return toWidgetEditable(div, viewWriter);
      },
    });

    // Convert the <avoindataSectionContent> model into an editable <div> widget.
    conversion.for('editingDowncast').elementToElement({
      model: 'avoindataSectionContent',
      view: (modelElement, { writer: viewWriter }) => {
        const div = viewWriter.createEditableElement('div', {
          class: 'avoindata-section-content',
        });
        return toWidgetEditable(div, viewWriter);
      },
    });
  }
}
