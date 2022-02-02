// it would be ideal if we could include the the cypress and artillery configs into a single file and utilize the name property
// this is pretty simple to do using the webpack cli (used for artillery), more time will be needed to find a clean way to acheive this with @cypress/webpack-preprocessor
import webpack from "webpack";
import CopyPlugin from "copy-webpack-plugin";
import dotenv from "dotenv";
import path from "path";

module.exports = () => {
  dotenv.config();

  const baseConfig = {
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
      "@influxdata/influxdb-client": "@influxdata/influxdb-client",
    },
    resolve: {
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

  return [
    {
      name: "processor",
      ...baseConfig,
      entry: {
        processor: "./src/artillery/processor.ts",
      },
      plugins: [
        new webpack.DefinePlugin({
          "process.env.DOCUMENT_FORMS": JSON.stringify("forms"),
        }),
        new CopyPlugin({
          patterns: [
            { from: "./src/artillery/package.json", to: "./" },
            { from: "./src/artillery/cloud.agents.yml", to: "./" },
            { from: "./src/artillery/cloud.claimants.yml", to: "./" },
            { from: "./src/artillery/development.yml", to: "./" },
          ],
        }),
      ],
    },
    {
      name: "reporter",
      ...baseConfig,
      entry: {
        influxdb: "./src/artillery/plugins/influxdb.ts",
      },
      output: {
        ...baseConfig.output,
        path: path.resolve(__dirname, "dist", "plugins"),
      },
    },
  ];
};
