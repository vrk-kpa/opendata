import { Plugin } from 'ckeditor5/src/core';
import { toWidget, toWidgetEditable } from 'ckeditor5/src/widget';
import { Widget } from 'ckeditor5/src/widget';
import InsertAvoindataHintCommand from './insertAvoindataHintCommand';
import icon from '../../icons/icon-hint.svg'

/**
 * CKEditor 5 plugins do not work directly with the DOM. They are defined as
 * plugin-specific data models that are then converted to markup that
 * is inserted in the DOM.
 *
 * CKEditor 5 internally interacts with expander as this model:
 * <avoindataHint>
 *   <avoindataHintHeader>
 *     <avoindataHintIcon/>
 *     <avoindataHintTitle></avoindataHintTitle>
 *   </avoindataHintHeader>
 *     <avoindataHintContent></avoindataHintContent>
 * </avoindataHint>
 *
 * Which is converted for the browser/user as this markup
 * <div class="avoindata-hint">
 *   <div class="avoindata-hint-header">
 *     <img class="avoindata-hint-icon" src="../icons/icon-hint.svg"/>
 *     <div class="avoindata-hint-title">Title</div>
 *   </div>
 *   <div class="avoindata-hint-content">Content</div>
 * </div>
 *
 * This file has the logic for defining the avoindataHint model, and for how it is
 * converted to standard DOM markup.
 */
export default class AvoindataHintEditing extends Plugin {
  static get requires() {
    return [Widget];
  }

  init() {
    this._defineSchema();
    this._defineConverters();
    this.editor.commands.add(
      'insertAvoindataHintCommand',
      new InsertAvoindataHintCommand(this.editor),
    );
  }

  /*
   * This registers the structure that will be seen by CKEditor 5 as
   * <avoindataHint>
   *   <avoindataHintHeader>
   *     <avoindataHintIcon/>
   *     <avoindataHintContent></avoindataHintContent>
   *   </avoindataHintHeader>
   * </avoindataHint>
   *
   * The logic in _defineConverters() will determine how this is converted to
   * markup.
   */
  _defineSchema() {
    // Schemas are registered via the central `editor` object.
    const schema = this.editor.model.schema;

    schema.register('avoindataHint', {
      // Behaves like a self-contained object (e.g. an image).
      isObject: true,
      // Allow in places where other blocks are allowed (e.g. directly in the root).
      allowWhere: '$block',
    });

    schema.register('avoindataHintIcon', {
      isObject: true,
      isContent: true,
      isInline: true,
      isBlock: false,
      isSelectable: false,
      isLimit: false,
      // This is only to be used within avoindataHint.
      allowIn: 'avoindataHint',
      allowAttributes: ['src', 'alt', 'class']
    });

    schema.register('avoindataHintContent', {
      isLimit: true,
      allowIn: 'avoindataHint',
      allowContentOf: '$root',
    });

    schema.addChildCheck((context, childDefinition) => {
      // Disallow avoindataHint inside avoindataHintContent.
      if (
        context.endsWith('avoindataHintContent') &&
        childDefinition.name === 'avoindataHint'
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
    // If <div class="avoindata-hint"> is present in the existing markup
    // processed by CKEditor, then CKEditor recognizes and loads it as a
    // <avoindataHint> model.
    conversion.for('upcast').elementToElement({
      model: 'avoindataHint',
      view: {
        name: 'div',
        classes: 'avoindata-hint',
      },
    });

    conversion.for('upcast').elementToElement({
      model: 'avoindataHintIcon',
      view: {
        name: 'img',
        classes: 'avoindata-hint-icon',
      },
    });

    // If <div class="avoindata-hint-content"> is present in the existing markup
    // processed by CKEditor, then CKEditor recognizes and loads it as a
    // <avoindataHintContent> model, provided it is a child element of
    // <avoindataHint>, as required by the schema.
    conversion.for('upcast').elementToElement({
      model: 'avoindataHintContent',
      view: {
        name: 'div',
        classes: 'avoindata-hint-content',
      },
    });

    // Data Downcast Converters: converts stored model data into HTML.
    // These trigger when content is saved.
    //
    // Instances of <avoindataHint> are saved as
    // <div class="avoindata-hint">{{inner content}}</div>.
    conversion.for('dataDowncast').elementToElement({
      model: 'avoindataHint',
      view: {
        name: 'div',
        classes: 'avoindata-hint',
      },
    });

    // Instances of <avoindataHintIcon> are saved as
    // <img class="avoindata-hint-icon" src="../icons/icon-hint.svg" alt="Avoindata Hint icon"></div>.
    conversion.for('downcast').elementToElement({
      model: 'avoindataHintIcon',
      view: (modelElement, { writer }) => {
        return writer.createEmptyElement('img', { class: "avoindata-hint-icon", src: icon })
      }
    });

    // Instances of <avoindataHintContent> are saved as
    // <div class="savoindata-hint-content">{{inner content}}</div>.
    conversion.for('dataDowncast').elementToElement({
      model: 'avoindataHintContent',
      view: {
        name: 'div',
        classes: 'avoindata-hint-content',
      },
    });

    // Editing Downcast Converters. These render the content to the user for
    // editing, i.e. this determines what gets seen in the editor. These trigger
    // after the Data Upcast Converters, and are re-triggered any time there
    // are changes to any of the models' properties.
    //
    // Convert the <avoindataHint> model into a container widget in the editor UI.
    conversion.for('editingDowncast').elementToElement({
      model: 'avoindataHint',
      view: (modelElement, { writer: viewWriter }) => {
        const section = viewWriter.createContainerElement('div', {
          class: 'avoindata-hint',
        });

        return toWidget(section, viewWriter, { label: 'Avoindata Hint' });
      },
    });

    // Convert the <avoindataHintContent> model into an editable <div> widget.
    conversion.for('editingDowncast').elementToElement({
      model: 'avoindataHintContent',
      view: (modelElement, { writer: viewWriter }) => {
        const div = viewWriter.createEditableElement('div', {
          class: 'avoindata-hint-content',
        });
        return toWidgetEditable(div, viewWriter);
      },
    });

    conversion.for('upcast').elementToElement({
      model: 'avoindataHintIcon',
      view: {
        name: 'img',
        classes: 'avoindata-hint-image',
      },
    });
  }
}
