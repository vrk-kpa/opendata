## This module is modified from the [CKEditor 5 plugin development starter template](https://git.drupalcode.org/project/ckeditor5_dev/-/tree/1.0.3/ckeditor5_plugin_starter_template)

To facilitate easier development of modules that provide CKEditor 5 plugins,
developers may copy the contents of this directory to the root of their module
directory. This provides the basic build tools and directory structure for
creating CKEditor 5 plugins within a contributed module, as well as a basic
working plugin based on the [CKEditor 5 block plugin tutorial](https://ckeditor.com/docs/ckeditor5/latest/framework/guides/tutorials/implementing-a-block-widget.html)
but with additional documentation and minor changes for better integration
with Drupal.

When Drupal updates to use newer versions of CKEditor 5, it may be necessary to
update any files copied from here to your module.

Plugin source should be added to `src/{pluginNameDirectory}` and the build tools expect this directory to include an
`index.js` file that exports one or more CKEditor 5 plugins.

In the module directory, run `npm install` to set up the necessary assets. The
initial run of `install` may take a few minutes, but subsequent builds will be
faster.

After installing dependencies, plugins can be built with `npm build`.
They will be built to `js/{pluginNameDirectory}.js`.
