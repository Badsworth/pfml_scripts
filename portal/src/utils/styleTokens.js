/**
 * Parse design system tokens (variables) from our CSS.
 * This depends on our CSS passing a JSON object in the
 * `content` property on the HTML :after pseudo-element
 * @see https://www.lullabot.com/articles/importing-css-breakpoints-into-javascript
 * @returns { object } key/value pairs representing a Sass variable
 */
function styleTokens() {
  const content =
    typeof document === "undefined" // only try parsing the CSS if we're running in the DOM
      ? ""
      : document.defaultView
          .getComputedStyle(document.querySelector("html"), ":after")
          .getPropertyValue("content");

  if (content) {
    try {
      const value = content
        .replace(/^["']/, "") // remove leading quote mark
        .replace(/["']$/, "") // remove trailing quote mark
        .replace(/\\/g, ""); // remove escaping characters

      const tokens = JSON.parse(value);
      return tokens;
    } catch (error) {
      console.error("Failed to parse CSS tokens as JSON, received:", content);
      console.error(error);
    }
  }

  // Fallback to no tokens so server-side compilation works,
  // and to gracefully handle a scenario where the CSS `content`
  // is malformed
  return {};
}

export default styleTokens;
