!function(e,n){"object"==typeof exports&&"object"==typeof module?module.exports=n():"function"==typeof define&&define.amd?define([],n):"object"==typeof exports?exports.CKEditor5=n():(e.CKEditor5=e.CKEditor5||{},e.CKEditor5.avoindataExample=n())}(self,(()=>(()=>{var __webpack_modules__={"./src/avoindataExample/avoindataExample.js":(__unused_webpack_module,__webpack_exports__,__webpack_require__)=>{"use strict";eval('__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   "default": () => (/* binding */ AvoindataExample)\n/* harmony export */ });\n/* harmony import */ var _avoindataExampleEditing__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./avoindataExampleEditing */ "./src/avoindataExample/avoindataExampleEditing.js");\n/* harmony import */ var _avoindataExampleUI__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./avoindataExampleUI */ "./src/avoindataExample/avoindataExampleUI.js");\n/* harmony import */ var ckeditor5_src_core__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ckeditor5/src/core */ "ckeditor5/src/core.js");\n/* harmony import */ var _css_styles_css__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../../css/styles.css */ "./css/styles.css");\n/**\n * @file This is what CKEditor refers to as a master (glue) plugin. Its role is\n * just to load the “editing” and “UI” components of this Plugin. Those\n * components could be included in this file, but\n *\n * I.e, this file\'s purpose is to integrate all the separate parts of the plugin\n * before it\'s made discoverable via index.js.\n */\n\n// The contents of AvoindataExampleUI and AvoindataExampleEditing could be included in this\n// file, but it is recommended to separate these concerns in different files.\n\n\n\n\n\nclass AvoindataExample extends ckeditor5_src_core__WEBPACK_IMPORTED_MODULE_2__.Plugin {\n  // Note that AvoindataExampleEditing and AvoindataExampleUI also extend `Plugin`, but these\n  // are not seen as individual plugins by CKEditor 5. CKEditor 5 will only\n  // discover the plugins explicitly exported in index.js.\n  static get requires() {\n    return [_avoindataExampleEditing__WEBPACK_IMPORTED_MODULE_0__["default"], _avoindataExampleUI__WEBPACK_IMPORTED_MODULE_1__["default"]];\n  }\n}\n\n\n//# sourceURL=webpack://CKEditor5.avoindataExample/./src/avoindataExample/avoindataExample.js?')},"./src/avoindataExample/avoindataExampleEditing.js":(__unused_webpack_module,__webpack_exports__,__webpack_require__)=>{"use strict";eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   \"default\": () => (/* binding */ AvoindataExampleEditing)\n/* harmony export */ });\n/* harmony import */ var ckeditor5_src_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ckeditor5/src/core */ \"ckeditor5/src/core.js\");\n/* harmony import */ var ckeditor5_src_widget__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ckeditor5/src/widget */ \"ckeditor5/src/widget.js\");\n/* harmony import */ var _insertAvoindataExampleCommand__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./insertAvoindataExampleCommand */ \"./src/avoindataExample/insertAvoindataExampleCommand.js\");\n\n\n\n\n\n/**\n * CKEditor 5 plugins do not work directly with the DOM. They are defined as\n * plugin-specific data models that are then converted to markup that\n * is inserted in the DOM.\n *\n * CKEditor 5 internally interacts with expander as this model:\n * <avoindataExample>\n *     <avoindataExampleTitle></avoindataExampleTitle>\n *     <avoindataExampleContent></avoindataExampleContent>\n * </avoindataExample>\n *\n * Which is converted for the browser/user as this markup\n * <div class=\"avoindata-example\">\n *   <div class=\"avoindata-example-header\">\n *     <div class=\"avoindata-example-title\">Title</div>\n *   </div>\n *   <div class=\"avoindata-example-content\">Content</div>\n * </div>\n *\n * This file has the logic for defining the avoindataExample model, and for how it is\n * converted to standard DOM markup.\n */\nclass AvoindataExampleEditing extends ckeditor5_src_core__WEBPACK_IMPORTED_MODULE_0__.Plugin {\n  static get requires() {\n    return [ckeditor5_src_widget__WEBPACK_IMPORTED_MODULE_1__.Widget];\n  }\n\n  init() {\n    this._defineSchema();\n    this._defineConverters();\n    this.editor.commands.add(\n      'insertAvoindataExampleCommand',\n      new _insertAvoindataExampleCommand__WEBPACK_IMPORTED_MODULE_2__[\"default\"](this.editor),\n    );\n  }\n\n  /*\n   * This registers the structure that will be seen by CKEditor 5 as\n   * <avoindataExample>\n   *     <avoindataExampleTitle></avoindataExampleTitle>\n   *     <avoindataExampleContent></avoindataExampleContent>\n   * </avoindataExample>\n   *\n   * The logic in _defineConverters() will determine how this is converted to\n   * markup.\n   */\n  _defineSchema() {\n    // Schemas are registered via the central `editor` object.\n    const schema = this.editor.model.schema;\n\n    schema.register('avoindataExample', {\n      // Behaves like a self-contained object (e.g. an image).\n      isObject: true,\n      // Allow in places where other blocks are allowed (e.g. directly in the root).\n      allowWhere: '$block',\n    });\n\n    schema.register('avoindataExampleTitle', {\n      // This creates a boundary for external actions such as clicking and\n      // and keypress. For example, when the cursor is inside this box, the\n      // keyboard shortcut for \"select all\" will be limited to the contents of\n      // the box.\n      isLimit: true,\n      // This is only to be used within avoindataExample.\n      allowIn: 'avoindataExample',\n      // Allow content that is allowed in blocks (e.g. text with attributes).\n      allowContentOf: '$root',\n    });\n\n    schema.register('avoindataExampleContent', {\n      isLimit: true,\n      allowIn: 'avoindataExample',\n      allowContentOf: '$root',\n    });\n\n    schema.addChildCheck((context, childDefinition) => {\n      // Disallow avoindataExample inside avoindataExampleContent.\n      if (\n        (context.endsWith('avoindataExampleContent') || context.endsWith('avoindataExampleTitle')) &&\n        childDefinition.name === 'avoindataExample'\n      ) {\n        return false;\n      }\n    });\n  }\n\n  /**\n   * Converters determine how CKEditor 5 models are converted into markup and\n   * vice-versa.\n   */\n  _defineConverters() {\n    // Converters are registered via the central editor object.\n    const { conversion } = this.editor;\n\n    // Upcast Converters: determine how existing HTML is interpreted by the\n    // editor. These trigger when an editor instance loads.\n    //\n    // If <div class=\"avoindata-example\"> is present in the existing markup\n    // processed by CKEditor, then CKEditor recognizes and loads it as a\n    // <avoindataExample> model.\n    conversion.for('upcast').elementToElement({\n      model: 'avoindataExample',\n      view: {\n        name: 'div',\n        classes: 'avoindata-example',\n      },\n    });\n\n    // If <div class=\"avoindata-example-title\"> is present in the existing markup\n    // processed by CKEditor, then CKEditor recognizes and loads it as a\n    // <avoindataExampleTitle> model, provided it is a child element of <avoindataExample>,\n    // as required by the schema.\n    conversion.for('upcast').elementToElement({\n      model: 'avoindataExampleTitle',\n      view: {\n        name: 'div',\n        classes: 'avoindata-example-title',\n      },\n    });\n\n    // If <div class=\"avoindata-example-content\"> is present in the existing markup\n    // processed by CKEditor, then CKEditor recognizes and loads it as a\n    // <avoindataExampleContent> model, provided it is a child element of\n    // <avoindataExample>, as required by the schema.\n    conversion.for('upcast').elementToElement({\n      model: 'avoindataExampleContent',\n      view: {\n        name: 'div',\n        classes: 'avoindata-example-content',\n      },\n    });\n\n    // Data Downcast Converters: converts stored model data into HTML.\n    // These trigger when content is saved.\n    //\n    // Instances of <avoindataExample> are saved as\n    // <div class=\"avoindata-example\">{{inner content}}</div>.\n    conversion.for('dataDowncast').elementToElement({\n      model: 'avoindataExample',\n      view: {\n        name: 'div',\n        classes: 'avoindata-example',\n      },\n    });\n\n    // Instances of <avoindataExampleTitle> are saved as\n    // <div class=\"avoindata-example-title\">{{inner content}}</div>.\n    conversion.for('dataDowncast').elementToElement({\n      model: 'avoindataExampleTitle',\n      view: {\n        name: 'div',\n        classes: 'avoindata-example-title',\n      },\n    });\n\n    // Instances of <avoindataExampleContent> are saved as\n    // <div class=\"savoindata-example-content\">{{inner content}}</div>.\n    conversion.for('dataDowncast').elementToElement({\n      model: 'avoindataExampleContent',\n      view: {\n        name: 'div',\n        classes: 'avoindata-example-content',\n      },\n    });\n\n    // Editing Downcast Converters. These render the content to the user for\n    // editing, i.e. this determines what gets seen in the editor. These trigger\n    // after the Data Upcast Converters, and are re-triggered any time there\n    // are changes to any of the models' properties.\n    //\n    // Convert the <avoindataExample> model into a container widget in the editor UI.\n    conversion.for('editingDowncast').elementToElement({\n      model: 'avoindataExample',\n      view: (modelElement, { writer: viewWriter }) => {\n        const section = viewWriter.createContainerElement('div', {\n          class: 'avoindata-example',\n        });\n\n        return (0,ckeditor5_src_widget__WEBPACK_IMPORTED_MODULE_1__.toWidget)(section, viewWriter, { label: 'Avoindata Example' });\n      },\n    });\n\n    // Convert the <avoindataExampleTitle> model into an editable <div> widget.\n    conversion.for('editingDowncast').elementToElement({\n      model: 'avoindataExampleTitle',\n      view: (modelElement, { writer: viewWriter }) => {\n        const div = viewWriter.createEditableElement('div', {\n          class: 'avoindata-example-title',\n        });\n        return (0,ckeditor5_src_widget__WEBPACK_IMPORTED_MODULE_1__.toWidgetEditable)(div, viewWriter);\n      },\n    });\n\n    // Convert the <avoindataExampleContent> model into an editable <div> widget.\n    conversion.for('editingDowncast').elementToElement({\n      model: 'avoindataExampleContent',\n      view: (modelElement, { writer: viewWriter }) => {\n        const div = viewWriter.createEditableElement('div', {\n          class: 'avoindata-example-content',\n        });\n        return (0,ckeditor5_src_widget__WEBPACK_IMPORTED_MODULE_1__.toWidgetEditable)(div, viewWriter);\n      },\n    });\n\n    // Extra converters for the older format ckeditor4 plugins\n    conversion.for('upcast').elementToElement({\n      model: 'avoindataExampleTitle',\n      view: {\n        name: 'h2',\n        classes: 'avoindata-example-title',\n      },\n    });\n\n    conversion.for('upcast').elementToElement({\n      model: 'avoindataExampleTitle',\n      view: {\n        name: 'h3',\n        classes: 'avoindata-example-title',\n      },\n    });\n  }\n}\n\n\n//# sourceURL=webpack://CKEditor5.avoindataExample/./src/avoindataExample/avoindataExampleEditing.js?")},"./src/avoindataExample/avoindataExampleUI.js":(__unused_webpack_module,__webpack_exports__,__webpack_require__)=>{"use strict";eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   \"default\": () => (/* binding */ AvoindataExampleUI)\n/* harmony export */ });\n/* harmony import */ var ckeditor5_src_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ckeditor5/src/core */ \"ckeditor5/src/core.js\");\n/* harmony import */ var ckeditor5_src_ui__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ckeditor5/src/ui */ \"ckeditor5/src/ui.js\");\n/* harmony import */ var _icons_icon_example_svg_source__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../../icons/icon-example.svg?source */ \"./icons/icon-example.svg?source\");\n/**\n * @file registers the avoindataExample toolbar button and binds functionality to it.\n */\n\n\n\n\n\nclass AvoindataExampleUI extends ckeditor5_src_core__WEBPACK_IMPORTED_MODULE_0__.Plugin {\n  init() {\n    const editor = this.editor;\n\n    // This will register the avoindataExample toolbar button.\n    editor.ui.componentFactory.add('avoindataExample', (locale) => {\n      const command = editor.commands.get('insertAvoindataExampleCommand');\n      const buttonView = new ckeditor5_src_ui__WEBPACK_IMPORTED_MODULE_1__.ButtonView(locale);\n\n      // Create the toolbar button.\n      buttonView.set({\n        label: editor.t('Avoindata Example'),\n        icon: _icons_icon_example_svg_source__WEBPACK_IMPORTED_MODULE_2__,\n        tooltip: true,\n      });\n\n      // Bind the state of the button to the command.\n      buttonView.bind('isOn', 'isEnabled').to(command, 'value', 'isEnabled');\n\n      // Execute the command when the button is clicked (executed).\n      this.listenTo(buttonView, 'execute', () =>\n        editor.execute('insertAvoindataExampleCommand'),\n      );\n\n      return buttonView;\n    });\n  }\n}\n\n\n//# sourceURL=webpack://CKEditor5.avoindataExample/./src/avoindataExample/avoindataExampleUI.js?")},"./src/avoindataExample/index.js":(__unused_webpack_module,__webpack_exports__,__webpack_require__)=>{"use strict";eval('__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)\n/* harmony export */ });\n/* harmony import */ var _avoindataExample__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./avoindataExample */ "./src/avoindataExample/avoindataExample.js");\n/**\n * @file The build process always expects an index.js file. Anything exported\n * here will be recognized by CKEditor 5 as an available plugin. Multiple\n * plugins can be exported in this one file.\n *\n * I.e. this file\'s purpose is to make plugin(s) discoverable.\n */\n\n\n\n/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = ({\n  AvoindataExample: _avoindataExample__WEBPACK_IMPORTED_MODULE_0__["default"],\n});\n\n\n//# sourceURL=webpack://CKEditor5.avoindataExample/./src/avoindataExample/index.js?')},"./src/avoindataExample/insertAvoindataExampleCommand.js":(__unused_webpack_module,__webpack_exports__,__webpack_require__)=>{"use strict";eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   \"default\": () => (/* binding */ InsertAvoindataExampleCommand)\n/* harmony export */ });\n/* harmony import */ var ckeditor5_src_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ckeditor5/src/core */ \"ckeditor5/src/core.js\");\n/**\n * @file defines InsertAvoindataExampleCommand, which is executed when the avoindataExample\n * toolbar button is pressed.\n */\n\n\n\nclass InsertAvoindataExampleCommand extends ckeditor5_src_core__WEBPACK_IMPORTED_MODULE_0__.Command {\n  execute() {\n    const { model } = this.editor;\n\n    model.change((writer) => {\n      // Insert <avoindataExample>*</avoindataExample> at the current selection position\n      // in a way that will result in creating a valid model structure.\n      const avoindataExample = createAvoindataExample(writer);\n      model.insertContent(avoindataExample);\n    });\n  }\n\n  refresh() {\n    const { model } = this.editor;\n    const { selection } = model.document;\n\n    // Determine if the cursor (selection) is in a position where adding a\n    // avoindataExample is permitted. This is based on the schema of the model(s)\n    // currently containing the cursor.\n    const allowedIn = model.schema.findAllowedParent(\n      selection.getFirstPosition(),\n      'avoindataExample',\n    );\n\n    // If the cursor is not in a location where a avoindataExample can be added, return\n    // null so the addition doesn't happen.\n    this.isEnabled = allowedIn !== null;\n  }\n}\n\nfunction createAvoindataExample(writer) {\n  // Create instances of the elements registered with the editor in\n  // avoindataexpanderediting.js.\n  const avoindataExample = writer.createElement('avoindataExample');\n  const avoindataExampleTitle = writer.createElement('avoindataExampleTitle');\n  const avoindataExampleContent = writer.createElement('avoindataExampleContent');\n\n  // Append the title and content elements to the avoindataExample, which matches\n  // the parent/child relationship as defined in their schemas.\n  writer.append(avoindataExampleTitle, avoindataExample);\n  writer.append(avoindataExampleContent, avoindataExample);\n\n  // The text content will automatically be wrapped in a\n  // `<p>`.\n  const title = writer.createElement('paragraph');\n  writer.insertText('Title', title, 0);\n  writer.append(title, avoindataExampleTitle);\n  const content = writer.createElement('paragraph');\n  writer.insertText('Content', content, 0);\n  writer.append(content, avoindataExampleContent);\n\n  // Return the element to be added to the editor.\n  return avoindataExample;\n}\n\n\n//# sourceURL=webpack://CKEditor5.avoindataExample/./src/avoindataExample/insertAvoindataExampleCommand.js?")},"./css/styles.css":(module,__unused_webpack_exports,__webpack_require__)=>{"use strict";eval('module.exports = __webpack_require__.p + "../css/styles.css";\n\n//# sourceURL=webpack://CKEditor5.avoindataExample/./css/styles.css?')},"./icons/icon-example.svg?source":module=>{"use strict";eval('module.exports = "<svg width=\\"24px\\" height=\\"24px\\" viewBox=\\"0 0 24 24\\" version=\\"1.1\\"\\n  xmlns=\\"http://www.w3.org/2000/svg\\"\\n  xmlns:xlink=\\"http://www.w3.org/1999/xlink\\">\\n  <g stroke-width=\\"1\\" fill-rule=\\"evenodd\\">\\n    <path d=\\"M0,0 L24,0 24,24 0,24 Z\\" id=\\"path-1\\" stroke=\\"#2a6ebb\\" stroke-width=\\"3\\" fill=\\"none\\"></path>\\n    <path d=\\"M0,0 L4,0 4,24 0,24 Z\\" id=\\"path-2\\" fill=\\"#2a6ebb\\"></path>\\n  </g>\\n</svg>\\n";\n\n//# sourceURL=webpack://CKEditor5.avoindataExample/./icons/icon-example.svg?')},"ckeditor5/src/core.js":(module,__unused_webpack_exports,__webpack_require__)=>{eval('module.exports = (__webpack_require__(/*! dll-reference CKEditor5.dll */ "dll-reference CKEditor5.dll"))("./src/core.js");\n\n//# sourceURL=webpack://CKEditor5.avoindataExample/delegated_./core.js_from_dll-reference_CKEditor5.dll?')},"ckeditor5/src/ui.js":(module,__unused_webpack_exports,__webpack_require__)=>{eval('module.exports = (__webpack_require__(/*! dll-reference CKEditor5.dll */ "dll-reference CKEditor5.dll"))("./src/ui.js");\n\n//# sourceURL=webpack://CKEditor5.avoindataExample/delegated_./ui.js_from_dll-reference_CKEditor5.dll?')},"ckeditor5/src/widget.js":(module,__unused_webpack_exports,__webpack_require__)=>{eval('module.exports = (__webpack_require__(/*! dll-reference CKEditor5.dll */ "dll-reference CKEditor5.dll"))("./src/widget.js");\n\n//# sourceURL=webpack://CKEditor5.avoindataExample/delegated_./widget.js_from_dll-reference_CKEditor5.dll?')},"dll-reference CKEditor5.dll":e=>{"use strict";e.exports=CKEditor5.dll}},__webpack_module_cache__={};function __webpack_require__(e){var n=__webpack_module_cache__[e];if(void 0!==n)return n.exports;var a=__webpack_module_cache__[e]={exports:{}};return __webpack_modules__[e](a,a.exports,__webpack_require__),a.exports}__webpack_require__.d=(e,n)=>{for(var a in n)__webpack_require__.o(n,a)&&!__webpack_require__.o(e,a)&&Object.defineProperty(e,a,{enumerable:!0,get:n[a]})},__webpack_require__.g=function(){if("object"==typeof globalThis)return globalThis;try{return this||new Function("return this")()}catch(e){if("object"==typeof window)return window}}(),__webpack_require__.o=(e,n)=>Object.prototype.hasOwnProperty.call(e,n),__webpack_require__.r=e=>{"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})},(()=>{var e;__webpack_require__.g.importScripts&&(e=__webpack_require__.g.location+"");var n=__webpack_require__.g.document;if(!e&&n&&(n.currentScript&&(e=n.currentScript.src),!e)){var a=n.getElementsByTagName("script");if(a.length)for(var t=a.length-1;t>-1&&!e;)e=a[t--].src}if(!e)throw new Error("Automatic publicPath is not supported in this browser");e=e.replace(/#.*$/,"").replace(/\?.*$/,"").replace(/\/[^\/]+$/,"/"),__webpack_require__.p=e})();var __webpack_exports__=__webpack_require__("./src/avoindataExample/index.js");return __webpack_exports__=__webpack_exports__.default,__webpack_exports__})()));