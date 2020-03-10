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

module.exports = {
  addons: ["@storybook/addon-docs"],
  stories: ["../src/**/*.stories.js", "./stories/**/*.stories.js"],
  /**
   * Customize the Webpack configuration used by Storybook so it supports
   * Sass files.
   * @param {Object} config - Default Storybook Webpack config
   * @param {Object} options
   * @param {"DEVELOPMENT"|"PRODUCTION"} options.configType - 'PRODUCTION' is used
   *  when building the static version of storybook.
   * @returns {Object} Altered Webpack config
   */
  webpackFinal: async (config, { configType }) => {
    config.module.rules.push({
      test: /\.scss$/,
      use: [
        "style-loader",
        "css-loader",
        {
          loader: "sass-loader",
          options: nextConfig.sassLoaderOptions,
        },
      ],
      include: path.resolve(__dirname, "../"),
    });

    return config;
  },
};
