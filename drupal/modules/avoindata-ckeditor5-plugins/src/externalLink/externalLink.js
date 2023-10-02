import { Plugin } from 'ckeditor5/src/core';

export default class ExternalLink extends Plugin {
  init() {
    /*
    const editor = this.editor;

    // `listenTo()` and `editor` are available thanks to `Plugin`.
    // By using `listenTo()` you will ensure that the listener is removed when
    // the plugin is destroyed.
    this.listenTo(editor.data, 'ready', () => {
      const linkCommand = editor.commands.get('link');
      const { selection } = editor.model.document;

      let linkCommandExecuting = false;

      linkCommand.on('execute', (evt, args) => {
        const linkIsExternal = args[1]['linkIsExternal']

        if (linkIsExternal) {
          if (linkCommandExecuting) {
            linkCommandExecuting = false;
            return;
          }

          // If the additional attribute was passed, we stop the default execution
          // of the LinkCommand. We're going to create Model#change() block for undo
          // and execute the LinkCommand together with setting the extra attribute.
          evt.stop();

          // Prevent infinite recursion by keeping records of when link command is
          // being executed by this function.
          linkCommandExecuting = true;

          // Wrapping the original command execution in a model.change() block to make sure there's a single undo step
          // when the extra attribute is added.

          editor.model.change(writer => {
            editor.execute('link', ...args);
            const link = selection.getLastPosition().nodeBefore;
            // writer.insertElement('avoindataExternalLink', selection.getLastPosition())
          });
        }
      })
    });
    */
  }

  static get pluginName() {
    return 'ExternalLink';
  }
}
