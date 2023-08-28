import { Plugin } from 'ckeditor5/src/core';
import { toWidget, toWidgetEditable } from 'ckeditor5/src/widget';
import { Widget } from 'ckeditor5/src/widget';
import InsertAvoindataNoteCommand from './insertAvoindataNoteCommand';
import icon from '../../icons/icon-info.svg';


/**
 * CKEditor 5 plugins do not work directly with the DOM. They are defined as
 * plugin-specific data models that are then converted to markup that
 * is inserted in the DOM.
 *
 * CKEditor 5 internally interacts with expander as this model:
 * <avoindataNote>
 *   <avoindataNoteHeader>
 *     <avoindataNoteIcon/>
 *     <avoindataNoteTitle></avoindataNoteTitle>
 *   </avoindataNoteHeader>
 *     <avoindataNoteContent></avoindataNoteContent>
 * </avoindataNote>
 *
 * Which is converted for the browser/user as this markup
 * <div class="avoindata-note">
 *   <div class="avoindata-note-header">
 *     <img class="avoindata-note-icon" src="../icons/icon-info.svg"/>
 *     <div class="avoindata-note-title">Title</div>
 *   </div>
 *   <div class="avoindata-note-content">Content</div>
 * </div>
 *
 * This file has the logic for defining the avoindataNote model, and for how it is
 * converted to standard DOM markup.
 */
export default class AvoindataNoteEditing extends Plugin {
  static get requires() {
    return [Widget];
  }

  init() {
    this._defineSchema();
    this._defineConverters();
    this.editor.commands.add(
      'insertAvoindataNoteCommand',
      new InsertAvoindataNoteCommand(this.editor),
    );
  }

  /*
   * This registers the structure that will be seen by CKEditor 5 as
   * <avoindataNote>
   *   <avoindataNoteHeader>
   *     <avoindataNoteIcon/>
   *     <avoindataNoteTitle></avoindataNoteTitle>
   *   </avoindataNoteHeader>
   *     <avoindataNoteContent></avoindataNoteContent>
   * </avoindataNote>
   *
   * The logic in _defineConverters() will determine how this is converted to
   * markup.
   */
  _defineSchema() {
    // Schemas are registered via the central `editor` object.
    const schema = this.editor.model.schema;

    schema.register('avoindataNote', {
      // Behaves like a self-contained object (e.g. an image).
      isObject: true,
      // Allow in places where other blocks are allowed (e.g. directly in the root).
      allowWhere: '$block',
    });

    schema.register('avoindataNoteHeader', {
      // This is only to be used within avoindataNote.
      isObject: true,
      isSelectable: false,
      allowIn: 'avoindataNote',
      allowChildren: ['avoindataNoteIcon', 'avoindataNoteTitle']
    });

    schema.register('avoindataNoteIcon', {
      isObject: true,
      isContent: true,
      isInline: true,
      isBlock: false,
      isSelectable: false,
      isLimit: false,
      // This is only to be used within avoindataNote.
      allowIn: 'avoindataNoteHeader',
      allowAttributes: ['src', 'alt', 'class']
    });

    schema.register('avoindataNoteTitle', {
      // This creates a boundary for external actions such as clicking and
      // and keypress. For example, when the cursor is inside this box, the
      // keyboard shortcut for "select all" will be limited to the contents of
      // the box.
      isLimit: true,
      // This is only to be used within avoindataNote.
      allowIn: 'avoindataNoteHeader',
      // Allow content that is allowed in blocks (e.g. text with attributes).
      allowContentOf: '$root',
    });

    schema.register('avoindataNoteContent', {
      isLimit: true,
      allowIn: 'avoindataNote',
      allowContentOf: '$root',
    });

    schema.addChildCheck((context, childDefinition) => {
      // Disallow avoindataNote inside avoindataNoteContent.
      if (
        (context.endsWith('avoindataNoteContent') || context.endsWith('avoindataNoteTitle')) &&
        childDefinition.name === 'avoindataNote'
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
    // If <div class="avoindata-note"> is present in the existing markup
    // processed by CKEditor, then CKEditor recognizes and loads it as a
    // <avoindataNote> model.
    conversion.for('upcast').elementToElement({
      model: 'avoindataNote',
      view: {
        name: 'div',
        classes: 'avoindata-note',
      },
    });

    conversion.for('upcast').elementToElement({
      model: 'avoindataNoteHeader',
      view: {
        name: 'div',
        classes: 'avoindata-note-header',
      },
    });

    conversion.for('upcast').elementToElement({
      model: 'avoindataNoteIcon',
      view: {
        name: 'img',
        classes: 'avoindata-note-icon'
      },
    });

    // If <div class="avoindata-note-title"> is present in the existing markup
    // processed by CKEditor, then CKEditor recognizes and loads it as a
    // <avoindataNoteTitle> model, provided it is a child element of <avoindataNote>,
    // as required by the schema.
    conversion.for('upcast').elementToElement({
      model: 'avoindataNoteTitle',
      view: {
        name: 'div',
        classes: 'avoindata-note-title',
      },
    });

    // If <div class="avoindata-note-content"> is present in the existing markup
    // processed by CKEditor, then CKEditor recognizes and loads it as a
    // <avoindataNoteContent> model, provided it is a child element of
    // <avoindataNote>, as required by the schema.
    conversion.for('upcast').elementToElement({
      model: 'avoindataNoteContent',
      view: {
        name: 'div',
        classes: 'avoindata-note-content',
      },
    });

    // Data Downcast Converters: converts stored model data into HTML.
    // These trigger when content is saved.
    //
    // Instances of <avoindataNote> are saved as
    // <div class="avoindata-note">{{inner content}}</div>.
    conversion.for('dataDowncast').elementToElement({
      model: 'avoindataNote',
      view: {
        name: 'div',
        classes: 'avoindata-note',
      },
    });

    // Instances of <avoindataNoteHeader> are saved as
    // <div class="avoindata-note-header">{{inner content}}</div>.
    conversion.for('dataDowncast').elementToElement({
      model: 'avoindataNoteHeader',
      view: {
        name: 'div',
        classes: 'avoindata-note-header',
      },
    });

    // Instances of <avoindataNoteIcon> are saved as
    // <img class="avoindata-note-icon" src="../icons/icon-info.svg" alt="Avoindata Note icon"></div>.
    conversion.for('dataDowncast').elementToElement({
      model: 'avoindataNoteIcon',
      view: (modelElement, { writer }) => {
        return writer.createUIElement('img', { class: 'avoindata-note-icon', src: icon, alt: "Avoindata Note icon" });
      }
    });

    // Instances of <avoindataNoteTitle> are saved as
    // <div class="avoindata-note-title">{{inner content}}</div>.
    conversion.for('dataDowncast').elementToElement({
      model: 'avoindataNoteTitle',
      view: {
        name: 'div',
        classes: 'avoindata-note-title',
      },
    });

    // Instances of <avoindataNoteContent> are saved as
    // <div class="savoindata-note-content">{{inner content}}</div>.
    conversion.for('dataDowncast').elementToElement({
      model: 'avoindataNoteContent',
      view: {
        name: 'div',
        classes: 'avoindata-note-content',
      },
    });

    // Editing Downcast Converters. These render the content to the user for
    // editing, i.e. this determines what gets seen in the editor. These trigger
    // after the Data Upcast Converters, and are re-triggered any time there
    // are changes to any of the models' properties.
    //
    // Convert the <avoindataNote> model into a container widget in the editor UI.
    conversion.for('editingDowncast').elementToElement({
      model: 'avoindataNote',
      view: (modelElement, { writer: viewWriter }) => {
        const section = viewWriter.createContainerElement('div', {
          class: 'avoindata-note',
        });

        return toWidget(section, viewWriter, { label: 'Avoindata Note widget' });
      },
    });

    // Convert the <avoindataNoteHeader> model into a container element in the editor UI.
    conversion.for('editingDowncast').elementToElement({
      model: 'avoindataNoteHeader',
      view: (modelElement, { writer: viewWriter }) => {
        return viewWriter.createContainerElement('div', {
          class: 'avoindata-note-header',
        });
      },
    });

    // Convert the <avoindataNoteIcon> model into an UI element in the editor UI.
    conversion.for('editingDowncast').elementToStructure({
      model: 'avoindataNoteIcon',
      view: (modelElement, { writer }) => {
        return writer.createUIElement('img', { class: 'avoindata-note-icon', src: icon, alt: "Avoindata Note icon" });
      },
    });

    // Convert the <avoindataNoteTitle> model into an editable <div> widget.
    conversion.for('editingDowncast').elementToElement({
      model: 'avoindataNoteTitle',
      view: (modelElement, { writer: viewWriter }) => {
        const div = viewWriter.createEditableElement('div', {
          class: 'avoindata-note-title',
        });
        return toWidgetEditable(div, viewWriter);
      },
    });

    // Convert the <avoindataNoteContent> model into an editable <div> widget.
    conversion.for('editingDowncast').elementToElement({
      model: 'avoindataNoteContent',
      view: (modelElement, { writer: viewWriter }) => {
        const div = viewWriter.createEditableElement('div', {
          class: 'avoindata-note-content',
        });
        return toWidgetEditable(div, viewWriter);
      },
    });
  }
}
