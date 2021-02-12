/**
 * Make a File instance
 * @see https://developer.mozilla.org/en-US/docs/Web/API/File
 * @param {object} attrs File attributes
 * @param {string} attrs.name The file's name
 * @param {string} attrs.type The file's MIME type
 * @returns {File}
 */
export const makeFile = (attrs = {}) => {
  const { name, type } = Object.assign(
    {
      name: "file.pdf",
      type: "application/pdf",
    },
    attrs
  );

  return new File([], name, { type });
};

/**
 * Create an HTML <input> for a test's event.target
 * @param {object} attrs - HTML attributes for the input
 * @returns {HTMLInputElement}
 */
export function createInputElement(attrs) {
  const input = document.createElement("input");

  Object.entries(attrs).forEach(([attributeName, value]) => {
    input.setAttribute(attributeName, value);
  });

  if (attrs.checked === false) input.checked = false;

  return input;
}
