// it would be ideal if we could include the the cypress and artillery configs into a single file and utilize the name property
// this is pretty simple to do using the webpack cli (used for artillery), more time will be needed to find a clean way to acheive this with @cypress/webpack-preprocessor
import TsconfigPathsPlugin from "tsconfig-paths-webpack-plugin";
import webpack from "webpack";
import CopyPlugin from "copy-webpack-plugin";
import dotenv from "dotenv";
module.exports = () => {
  dotenv.config();
  return {
    name: "artillery",
    mode: "development",
    entry: {
      processor: "./src/artillery/processor.ts",
    },
    output: {
      libraryTarget: "commonjs2",
    },
    target: "node",
    node: {
      // @todo: Webpack 5 has an eval-only version of this. That would be much better, as this
      // one operates on absolute paths.
      __dirname: true,
    },
    externals: {
      "playwright-chromium": "playwright-chromium",
    },
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
    plugins: [
      new webpack.DefinePlugin({
        "process.env.DOCUMENT_FORMS": JSON.stringify("forms"),
      }),
      new CopyPlugin({
        patterns: [
          { from: "./.env", to: "./" },
          { from: "./employees/*.employees.json", to: "./" },
          { from: "./forms/*.pdf", to: "./" },
          { from: "./src/artillery/package.json", to: "./" },
          { from: "./src/artillery/spec.yml", to: "./" },
        ],
      }),
      new webpack.EnvironmentPlugin({
        E2E_ENVIRONMENT: process.env.E2E_ENVIRONMENT,
      }),
    ],
  };
};
