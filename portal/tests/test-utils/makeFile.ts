/**
 * Make a File instance
 * @see https://developer.mozilla.org/en-US/docs/Web/API/File
 */
export const makeFile = (attrs?: { name?: string; type?: string }): File => {
  const { name, type } = Object.assign(
    {
      name: "file.pdf",
      type: "application/pdf",
    },
    attrs ?? {}
  );

  return new File([], name, { type });
};

/**
 * Create an HTML <input> for a test's event.target
 */
export function createInputElement(attrs: {
  [key: string]: boolean | string | number;
}) {
  const input: HTMLInputElement = document.createElement("input");

  Object.entries(attrs).forEach(([attributeName, value]) => {
    input.setAttribute(attributeName, value.toString());
  });

  if (attrs.checked === false) input.checked = false;

  return input;
}
