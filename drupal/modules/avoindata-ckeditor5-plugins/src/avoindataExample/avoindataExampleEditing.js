import { Plugin } from 'ckeditor5/src/core';
import { toWidget, toWidgetEditable } from 'ckeditor5/src/widget';
import { Widget } from 'ckeditor5/src/widget';
import InsertAvoindataExampleCommand from './insertAvoindataExampleCommand';

/**
 * CKEditor 5 plugins do not work directly with the DOM. They are defined as
 * plugin-specific data models that are then converted to markup that
 * is inserted in the DOM.
 *
 * CKEditor 5 internally interacts with expander as this model:
 * <avoindataExample>
 *     <avoindataExampleTitle></avoindataExampleTitle>
 *     <avoindataExampleContent></avoindataExampleContent>
 * </avoindataExample>
 *
 * Which is converted for the browser/user as this markup
 * <div class="avoindata-example">
 *   <div class="avoindata-example-header">
 *     <div class="avoindata-example-title">Title</div>
 *   </div>
 *   <div class="avoindata-example-content">Content</div>
 * </div>
 *
 * This file has the logic for defining the avoindataExample model, and for how it is
 * converted to standard DOM markup.
 */
export default class AvoindataExampleEditing extends Plugin {
  static get requires() {
    return [Widget];
  }

  init() {
    this._defineSchema();
    this._defineConverters();
    this.editor.commands.add(
      'insertAvoindataExampleCommand',
      new InsertAvoindataExampleCommand(this.editor),
    );
  }

  /*
   * This registers the structure that will be seen by CKEditor 5 as
   * <avoindataExample>
   *     <avoindataExampleTitle></avoindataExampleTitle>
   *     <avoindataExampleContent></avoindataExampleContent>
   * </avoindataExample>
   *
   * The logic in _defineConverters() will determine how this is converted to
   * markup.
   */
  _defineSchema() {
    // Schemas are registered via the central `editor` object.
    const schema = this.editor.model.schema;

    schema.register('avoindataExample', {
      // Behaves like a self-contained object (e.g. an image).
      isObject: true,
      // Allow in places where other blocks are allowed (e.g. directly in the root).
      allowWhere: '$block',
    });

    schema.register('avoindataExampleTitle', {
      // This creates a boundary for external actions such as clicking and
      // and keypress. For example, when the cursor is inside this box, the
      // keyboard shortcut for "select all" will be limited to the contents of
      // the box.
      isLimit: true,
      // This is only to be used within avoindataExample.
      allowIn: 'avoindataExample',
      // Allow content that is allowed in blocks (e.g. text with attributes).
      allowContentOf: '$root',
    });

    schema.register('avoindataExampleContent', {
      isLimit: true,
      allowIn: 'avoindataExample',
      allowContentOf: '$root',
    });

    schema.addChildCheck((context, childDefinition) => {
      // Disallow avoindataExample inside avoindataExampleContent.
      if (
        (context.endsWith('avoindataExampleContent') || context.endsWith('avoindataExampleTitle')) &&
        childDefinition.name === 'avoindataExample'
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
    // If <div class="avoindata-example"> is present in the existing markup
    // processed by CKEditor, then CKEditor recognizes and loads it as a
    // <avoindataExample> model.
    conversion.for('upcast').elementToElement({
      model: 'avoindataExample',
      view: {
        name: 'div',
        classes: 'avoindata-example',
      },
    });

    // If <div class="avoindata-example-title"> is present in the existing markup
    // processed by CKEditor, then CKEditor recognizes and loads it as a
    // <avoindataExampleTitle> model, provided it is a child element of <avoindataExample>,
    // as required by the schema.
    conversion.for('upcast').elementToElement({
      model: 'avoindataExampleTitle',
      view: {
        name: 'div',
        classes: 'avoindata-example-title',
      },
    });

    // If <div class="avoindata-example-content"> is present in the existing markup
    // processed by CKEditor, then CKEditor recognizes and loads it as a
    // <avoindataExampleContent> model, provided it is a child element of
    // <avoindataExample>, as required by the schema.
    conversion.for('upcast').elementToElement({
      model: 'avoindataExampleContent',
      view: {
        name: 'div',
        classes: 'avoindata-example-content',
      },
    });

    // Data Downcast Converters: converts stored model data into HTML.
    // These trigger when content is saved.
    //
    // Instances of <avoindataExample> are saved as
    // <div class="avoindata-example">{{inner content}}</div>.
    conversion.for('dataDowncast').elementToElement({
      model: 'avoindataExample',
      view: {
        name: 'div',
        classes: 'avoindata-example',
      },
    });

    // Instances of <avoindataExampleTitle> are saved as
    // <div class="avoindata-example-title">{{inner content}}</div>.
    conversion.for('dataDowncast').elementToElement({
      model: 'avoindataExampleTitle',
      view: {
        name: 'div',
        classes: 'avoindata-example-title',
      },
    });

    // Instances of <avoindataExampleContent> are saved as
    // <div class="savoindata-example-content">{{inner content}}</div>.
    conversion.for('dataDowncast').elementToElement({
      model: 'avoindataExampleContent',
      view: {
        name: 'div',
        classes: 'avoindata-example-content',
      },
    });

    // Editing Downcast Converters. These render the content to the user for
    // editing, i.e. this determines what gets seen in the editor. These trigger
    // after the Data Upcast Converters, and are re-triggered any time there
    // are changes to any of the models' properties.
    //
    // Convert the <avoindataExample> model into a container widget in the editor UI.
    conversion.for('editingDowncast').elementToElement({
      model: 'avoindataExample',
      view: (modelElement, { writer: viewWriter }) => {
        const section = viewWriter.createContainerElement('div', {
          class: 'avoindata-example',
        });

        return toWidget(section, viewWriter, { label: 'Avoindata Example widget' });
      },
    });

    // Convert the <avoindataExampleTitle> model into an editable <div> widget.
    conversion.for('editingDowncast').elementToElement({
      model: 'avoindataExampleTitle',
      view: (modelElement, { writer: viewWriter }) => {
        const div = viewWriter.createEditableElement('div', {
          class: 'avoindata-example-title',
        });
        return toWidgetEditable(div, viewWriter);
      },
    });

    // Convert the <avoindataExampleContent> model into an editable <div> widget.
    conversion.for('editingDowncast').elementToElement({
      model: 'avoindataExampleContent',
      view: (modelElement, { writer: viewWriter }) => {
        const div = viewWriter.createEditableElement('div', {
          class: 'avoindata-example-content',
        });
        return toWidgetEditable(div, viewWriter);
      },
    });
  }
}
