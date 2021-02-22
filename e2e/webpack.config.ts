import TsconfigPathsPlugin from "tsconfig-paths-webpack-plugin";

module.exports = {
  mode: "development",
  resolve: {
    // @see https://medium.com/better-programming/the-right-usage-of-aliases-in-webpack-typescript-4418327f47fa
    plugins: [new TsconfigPathsPlugin()],
    extensions: [".ts", ".js"],
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
