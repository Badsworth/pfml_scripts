import { invert } from "lodash";

/**
 * Get the first key in an object that has a value matching `value`
 * @param {object} collection
 * @param {string|number} targetValue
 * @returns {string}
 */
function findKeyByValue(collection, targetValue) {
  return invert(collection)[targetValue];
}

export default findKeyByValue;
