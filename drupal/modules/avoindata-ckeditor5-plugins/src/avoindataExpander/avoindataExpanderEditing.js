import { Plugin } from 'ckeditor5/src/core';
import { toWidget, toWidgetEditable } from 'ckeditor5/src/widget';
import { Widget } from 'ckeditor5/src/widget';
import InsertAvoindataExpanderCommand from './insertAvoindataExpanderCommand';

/**
 * CKEditor 5 plugins do not work directly with the DOM. They are defined as
 * plugin-specific data models that are then converted to markup that
 * is inserted in the DOM.
 *
 * CKEditor 5 internally interacts with expander as this model:
 * <avoindataExpander>
 *    <avoindataExpanderTitle></avoindataExpanderTitle>
 *    <avoindataExpanderContent></avoindataExpanderContent>
 * </avoindataExpander>
 *
 * Which is converted for the browser/user as this markup
 * <div class="avoindata-expander">
      <div class="avoindata-expander-header">
        <div class="avoindata-expander-title">Title</div>
          <span class="icon-wrapper pull-right"><i class="fas fa-angle-down"></i></span>
        </div>
        <div class="avoindata-expander-content">Content</div>
      </div>
 *
 * This file has the logic for defining the avoindataExpander model, and for how it is
 * converted to standard DOM markup.
 */
export default class AvoindataExpanderEditing extends Plugin {
  static get requires() {
    return [Widget];
  }

  init() {
    this._defineSchema();
    this._defineConverters();
    this.editor.commands.add(
      'insertAvoindataExpanderCommand',
      new InsertAvoindataExpanderCommand(this.editor),
    );
  }

  /*
   * This registers the structure that will be seen by CKEditor 5 as
   * <avoindataExpander>
   *   <avoindataExpanderTitle></avoindataExpanderTitle>
   *   <avoindataExpanderContent></avoindataExpanderContent>
   * </avoindataExpander>
   *
   * The logic in _defineConverters() will determine how this is converted to
   * markup.
   */
  _defineSchema() {
    // Schemas are registered via the central `editor` object.
    const schema = this.editor.model.schema;

    schema.register('avoindataExpander', {
      // Behaves like a self-contained object (e.g. an image).
      isObject: true,
      // Allow in places where other blocks are allowed (e.g. directly in the root).
      allowWhere: '$block',
    });

    schema.register('avoindataExpanderTitle', {
      // This creates a boundary for external actions such as clicking and
      // and keypress. For example, when the cursor is inside this box, the
      // keyboard shortcut for "select all" will be limited to the contents of
      // the box.
      isLimit: true,
      // This is only to be used within simpleBox.
      allowIn: 'avoindataExpander',
      // Allow content that is allowed in blocks (e.g. text with attributes).
      allowContentOf: '$root',
    });

    schema.register('avoindataExpanderContent', {
      isLimit: true,
      allowIn: 'avoindataExpander',
      allowContentOf: '$root',
    });

    schema.addChildCheck((context, childDefinition) => {
      // Disallow avoindataExpander inside avoindataExpanderContent.
      if (
        (context.endsWith('avoindataExpanderContent') || context.endsWith('avoindataExpanderTitle')) &&
        childDefinition.name === 'avoindataExpander'
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
    // If <div class="avoindata-expander"> is present in the existing markup
    // processed by CKEditor, then CKEditor recognizes and loads it as a
    // <simpleBox> model.
    conversion.for('upcast').elementToElement({
      model: 'avoindataExpander',
      view: {
        name: 'div',
        classes: 'avoindata-expander',
      },
    });

    // If <div class="avoindata-expander-title"> is present in the existing markup
    // processed by CKEditor, then CKEditor recognizes and loads it as a
    // <avoindataExpanderTitle> model, provided it is a child element of <avoindataExpander>,
    // as required by the schema.
    conversion.for('upcast').elementToElement({
      model: 'avoindataExpanderTitle',
      view: {
        name: 'div',
        classes: 'avoindata-expander-title',
      },
    });

    // If <div class="avoindata-expander-content"> is present in the existing markup
    // processed by CKEditor, then CKEditor recognizes and loads it as a
    // <avoindataExpanderContent> model, provided it is a child element of
    // <avoindataExpander>, as required by the schema.
    conversion.for('upcast').elementToElement({
      model: 'avoindataExpanderContent',
      view: {
        name: 'div',
        classes: 'avoindata-expander-content',
      },
    });

    // Data Downcast Converters: converts stored model data into HTML.
    // These trigger when content is saved.
    //
    // Instances of <avoindataExpander> are saved as
    // <div class="avoindata-expander">{{inner content}}</div>.
    conversion.for('dataDowncast').elementToElement({
      model: 'avoindataExpander',
      view: {
        name: 'div',
        classes: 'avoindata-expander',
      },
    });

    // Instances of <avoindataExpanderTitle> are saved as
    // <div class="avoindata-expander-title">{{inner content}}</div>.
    conversion.for('dataDowncast').elementToStructure({
      model: 'avoindataExpanderTitle',
      view: (modelElement, { writer }) => {
        return writer.createContainerElement('div', { class: 'avoindata-expander-header' }, [
          writer.createContainerElement('div', { class: 'avoindata-expander-title' }, [
            writer.createSlot()
          ]),
          writer.createContainerElement('span', { class: 'icon-wrapper pull-right' }, [
            writer.createEmptyElement('i', { class: 'fas fa-angle-down' })
          ])
        ])
      }
    });

    // Instances of <avoindataExpanderContent> are saved as
    // <div class="savoindata-expander-content">{{inner content}}</div>.
    conversion.for('dataDowncast').elementToElement({
      model: 'avoindataExpanderContent',
      view: {
        name: 'div',
        classes: 'avoindata-expander-content',
      },
    });

    // Editing Downcast Converters. These render the content to the user for
    // editing, i.e. this determines what gets seen in the editor. These trigger
    // after the Data Upcast Converters, and are re-triggered any time there
    // are changes to any of the models' properties.
    //
    // Convert the <avoindataExpander> model into a container widget in the editor UI.
    conversion.for('editingDowncast').elementToElement({
      model: 'avoindataExpander',
      view: (modelElement, { writer: viewWriter }) => {
        const section = viewWriter.createContainerElement('div', {
          class: 'avoindata-expander',
        });

        return toWidget(section, viewWriter, { label: 'Avoindata Expander widget' });
      },
    });

    // Convert the <avoindataExpanderTitle> model into an editable <div> widget.
    conversion.for('editingDowncast').elementToElement({
      model: 'avoindataExpanderTitle',
      view: (modelElement, { writer: viewWriter }) => {
        const div = viewWriter.createEditableElement('div', {
          class: 'avoindata-expander-title',
        });
        return toWidgetEditable(div, viewWriter);
      },
    });

    // Convert the <avoindataExpanderContent> model into an editable <div> widget.
    conversion.for('editingDowncast').elementToElement({
      model: 'avoindataExpanderContent',
      view: (modelElement, { writer: viewWriter }) => {
        const div = viewWriter.createEditableElement('div', {
          class: 'avoindata-expander-content',
        });
        return toWidgetEditable(div, viewWriter);
      },
    });
  }
}
