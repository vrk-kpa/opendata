const path = require('path');
const fs = require('fs');
const webpack = require('webpack');
const { styles, builds } = require('@ckeditor/ckeditor5-dev-utils');
const TerserPlugin = require('terser-webpack-plugin');

function getDirectories(srcpath) {
  return fs
    .readdirSync(srcpath)
    .filter((item) => fs.statSync(path.join(srcpath, item)).isDirectory());
}

module.exports = [];
// Loop through every subdirectory in src, each a different plugin, and build
// each one in ./build.
getDirectories('./src').forEach((dir) => {
  const bc = {
    mode: 'production',
    optimization: {
      minimize: true,
      minimizer: [
        new TerserPlugin({
          terserOptions: {
            format: {
              comments: false,
            },
          },
          test: /\.js(\?.*)?$/i,
          extractComments: false,
        }),
      ],
      moduleIds: 'named',
    },
    entry: {
      path: path.resolve(
        __dirname,
        'src',
        dir,
        'index.js',
      ),
    },
    output: {
      path: path.resolve(__dirname, './js'),
      filename: `${dir}.js`,
      library: ['CKEditor5', dir],
      libraryTarget: 'umd',
      libraryExport: 'default'
    },
    plugins: [
      // It is possible to require the ckeditor5-dll.manifest.json used in
      // core/node_modules rather than having to install CKEditor 5 here.
      // However, that requires knowing the location of that file relative to
      // where your module code is located.
      new webpack.DllReferencePlugin({
        manifest: require('ckeditor5/build/ckeditor5-dll.manifest.json'), // eslint-disable-line global-require, import/no-unresolved
        scope: 'ckeditor5/src',
        name: 'CKEditor5.dll',
      }),
    ],
    module: {
      rules: [
        {
          oneOf: [
            {
              test: /\.svg$/,
              resourceQuery: /source/,
              type: 'asset/source'
            },
            {
              test: /\.svg$/,
              type: "asset/resource",
              generator: {
                filename: '../icons/[base]'
              }
            },
            {
              test: /\.css$/,
              type: "asset/resource",
              generator: {
                filename: '../css/[base]'
              }
            }
          ]
        }]

    },
  };

  module.exports.push(bc);
});
