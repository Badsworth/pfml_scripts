import { invert } from "lodash";

/**
 * Get the first key in an object that has a value matching `value`
 */
function findKeyByValue(
  collection: Record<string, unknown>,
  targetValue: string
) {
  return invert(collection)[targetValue];
}

export default findKeyByValue;
