/* eslint sort-keys: ["error", "asc"] */

import BaseModel from "./BaseModel";

class PaymentPreference extends BaseModel {
  // @ts-expect-error ts-migrate(2416) FIXME: Property 'defaults' in type 'PaymentPreference' is... Remove this comment to see the full error message
  get defaults() {
    return {
      account_number: null,
      bank_account_type: null, // BankAccountType
      payment_method: null, // PaymentPreferenceMethod
      routing_number: null,
    };
  }
}

/**
 * Enums for the Application's `payment_preference.bank_account_type` field
 * @enum {string}
 */
export const BankAccountType = {
  checking: "Checking",
  savings: "Savings",
} as const;

/**
 * Enums for the Application's `payment_preference.payment_method` field
 * @enum {string}
 */
export const PaymentPreferenceMethod = {
  ach: "Elec Funds Transfer",
  check: "Check",
} as const;

export default PaymentPreference;
