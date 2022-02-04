module.exports = {
  mode: "development",
  resolve: {
    extensions: [".ts", ".js"],
    fallback: {
      path: require.resolve("path-browserify"),
    },
  },
  module: {
    rules: [
      {
        test: /\.[jt]s$/,
        exclude: [/node_modules/],
        use: [
          {
            loader: "babel-loader",
          },
        ],
      },
    ],
  },
};
