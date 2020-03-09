/**
 * @file PostCSS configuration file, used for defining how our CSS files are compiled.
 * @see https://github.com/postcss/postcss
 */
// Apply vendor prefixes for modern CSS syntax. Depends on browserslist file to determine target browsers.
const autoprefixer = require("autoprefixer");

module.exports = {
  plugins: [autoprefixer],
};
