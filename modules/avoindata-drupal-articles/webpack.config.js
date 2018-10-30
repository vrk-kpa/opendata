const path = require("path");

module.exports = {
  entry: "./src/js/main.js",
  output: {
    filename: "main.js",
    path: path.resolve(__dirname, "resources")
  },
  module: {
    rules: [
      {
        test: /\.m?js$/,
        include: [
          path.resolve(__dirname, "src")
        ],
        exclude: /(node_modules|bower_components)/,
        use: {
          loader: "babel-loader",
          options: {
            presets: [
              [
                "@babel/preset-env",
                {
                  targets: {
                    browsers: ["last 3 versions", "ie >= 11"]
                  },
                  useBuiltIns: "usage"
                }
              ]
            ]
          }
        }
      }
    ]
  }
};
