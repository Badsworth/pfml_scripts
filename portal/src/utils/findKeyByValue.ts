import { invert } from "lodash";

/**
 * Get the first key in an object that has a value matching `value`
 */
function findKeyByValue<TCollection extends { [key: string]: unknown }>(
  collection: TCollection,
  targetValue?: string | null
): keyof TCollection | undefined {
  if (!targetValue) return undefined;
  return invert(collection)[targetValue];
}

export default findKeyByValue;
