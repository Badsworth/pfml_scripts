/**
 * @file PostCSS configuration file, used for defining how our CSS files are compiled.
 * @see https://github.com/postcss/postcss
 */
// Apply vendor prefixes for modern CSS syntax. Depends on browserslist file to determine target browsers.
const autoprefixer = require("autoprefixer");
// postcss-sort-media-queries is required for USWDS utility classes to have the correct specificity (as of v2.4.0)
const sortMediaQueries = require("postcss-sort-media-queries");

module.exports = {
  plugins: [sortMediaQueries({ sort: "mobile-first" }), autoprefixer]
};
