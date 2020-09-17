/**
 * @file Storybook uses this file as its main configuration file.
 * It controls the generation of our Storybook. It concerns itself with the location of
 * story files, management of presets (which configure Webpack and Babel), and
 * generalized webpack configuration. You can also do basic addon registrations here.
 * @see https://medium.com/storybookjs/declarative-storybook-configuration-49912f77b78
 * @see https://storybook.js.org/docs/configurations/default-config/
 */
const path = require("path");
const nextConfig = require("../next.config");
const webpack = require("webpack");

module.exports = {
  addons: ["@storybook/addon-docs"],
  stories: ["./stories/**/*.stories.@(js|mdx)"],
  /**
   * Customize the Webpack configuration used by Storybook so it supports
   * Sass files and alias import paths.
   * @param {object} config - Default Storybook Webpack config
   * @param {object} options
   * @param {"DEVELOPMENT"|"PRODUCTION"} options.configType - 'PRODUCTION' is used
   *  when building the static version of storybook.
   * @returns {object} Altered Webpack config
   */
  webpackFinal: (config, { configType }) => {
    // Set our environment variables so things like Cognito integration works in the sandbox
    config.plugins.push(new webpack.EnvironmentPlugin(nextConfig.env));

    config.module.rules.push({
      test: /\.scss$/,
      use: [
        "style-loader",
        "css-loader",
        {
          loader: "sass-loader",
          options: {
            sassOptions: {
              includePaths: nextConfig.sassOptions.includePaths,
            },
          },
        },
      ],
      include: [path.resolve(__dirname, "../styles")],
    });

    // So that we can use the node.js __filename
    config.node = { __filename: true };

    // Simplify import paths in our Story files
    // For example, we can do:
    // import Foo from "src/components/Foo"
    // Instead of:
    // import Foo from "../../../src/components/Foo"
    config.resolve = config.resolve || {};
    config.resolve.alias = Object.assign(config.resolve.alias, {
      src: path.resolve(__dirname, "../src"),
      storybook: path.resolve(__dirname),
      tests: path.resolve(__dirname, "../tests"),
    });

    return config;
  },
};
