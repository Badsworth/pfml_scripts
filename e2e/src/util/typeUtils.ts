/**
 * @file Contains all of the type utils, like typeguards and assertions.
 * @author Sergei Kabuldzhanov <sergei@lastcallmedia.com>
 */

import {
  NonEmptyArray,
  RequiredKeys,
  ValidClaim,
  ValidConcurrentLeave,
  ValidEmployerBenefit,
  ValidOtherIncome,
  ValidPreviousLeave,
} from "../types";
import { DehydratedClaim } from "../generation/Claim";

// GENERIC UTILS

/**
 * Check whether a given value is neither null nor undefined.
 * @param arg - value to check
 * @example
 * isNotNull(null) => false
 * isNotNull("") => true
 */
export function isNotNull<T>(arg: T): arg is NonNullable<T> {
  return arg !== null && arg !== undefined;
}

/**
 * Assert given object has a defined property.
 * @param data
 * @param prop
 * @returns
 */
export function hasProp<K extends PropertyKey>(
  data: Record<PropertyKey, unknown>,
  prop: K
): data is Record<K, unknown> {
  return prop in data;
}

/**
 * Check whether a given value is an array where
 * each member is of a specified type
 * @param arr - array to check
 * @param check - type guard to use when evaluating each item
 * @example
 * isTypedArray(["", false, true], isNotNull)// true
 * isTypedArray([null, undefined], isNotNull)// false
 */
export function assertIsTypedArray<T>(
  arr: unknown,
  check: (x: unknown) => x is T
): asserts arr is NonEmptyArray<T> {
  if (!Array.isArray(arr)) throw new Error(`${arr} is not Array`);
  if (!arr.length) throw new Error(`${arr} should not be empty.`);
  if (arr.some((item) => !check(item)))
    throw new TypeError(`Item ${JSON.stringify(arr)} is not of required type.`);
}

/**
 * Returns assertion function for a given type and it's map of keys
 * @param map - uses an object so that it breaks if the type changes
 * @returns
 */
export function isObjectType<T>(map: Record<RequiredKeys<T>, string>) {
  return (arg: unknown): arg is T => {
    if (typeof arg !== "object") return false;
    if (!arg) return false;
    // Every key should not be null or undefined
    return Object.keys(map).every(
      (key) =>
        hasProp(arg as Record<PropertyKey, unknown>, key) &&
        isNotNull((arg as Record<PropertyKey, unknown>)[key])
    );
  };
}

// TYPE SPECIFIC UTILS

/**
 * @note In the following types, because we trust the values to actually be of the right type if they are present,
 * we are just checking that a object leave has all the required properties and they are not set to null.
 */

/**
 * Check value for the required previous leave properties.
 */
export const isValidPreviousLeave = isObjectType<ValidPreviousLeave>({
  is_for_current_employer: "",
  leave_end_date: "",
  leave_minutes: "",
  leave_reason: "",
  leave_start_date: "",
  type: "",
  worked_per_week_minutes: "",
});

/**
 * Check value for the required concurrent leave properties.
 */
export const isValidConcurrentLeave = isObjectType<ValidConcurrentLeave>({
  is_for_current_employer: "",
  leave_end_date: "",
  leave_start_date: "",
});

/**
 * Check value for the required other leave properties.
 */
export const isValidOtherIncome = isObjectType<ValidOtherIncome>({
  income_type: "",
  income_amount_dollars: "",
  income_amount_frequency: "",
  income_end_date: "",
  income_start_date: "",
});

/**
 * Check value for the required employer benefit properties.
 */
export const isValidEmployerBenefit = isObjectType<ValidEmployerBenefit>({
  benefit_start_date: "",
  benefit_end_date: "",
  benefit_amount_dollars: "",
  benefit_amount_frequency: "",
  benefit_type: "",
  is_full_salary_continuous: "",
});

/**
 * Asserts the existence of a set of properties on a generated claim
 * so that we don't have to check them everywhere within the E2E test suite.
 * @param claim - body of the generated application request.
 */
export function assertValidClaim(
  claim: DehydratedClaim["claim"]
): asserts claim is ValidClaim {
  const requiredProps: readonly RequiredKeys<ValidClaim>[] = [
    "employer_fein",
    "first_name",
    "last_name",
    "date_of_birth",
    "tax_identifier",
    "leave_details",
  ] as const;

  for (const key of requiredProps) {
    if (!isNotNull(claim[key])) throw new TypeError(`Claim missing ${key}`);
  }
  return;
}
