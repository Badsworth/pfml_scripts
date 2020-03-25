/**
 * Use this to set most React input field values. React inputs won't
 * work as you'd expect if they have a `null` value, and this method
 * helps avoid forgetting to check if a value is set.
 * @param {boolean|number|string} initialValue
 * @param {boolean|number|string} [fallback]
 * @returns {boolean|number|string}
 */
function valueWithFallback(initialValue, fallback = "") {
  return initialValue || fallback;
}

export default valueWithFallback;
