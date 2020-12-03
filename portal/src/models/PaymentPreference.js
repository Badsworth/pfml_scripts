/* eslint sort-keys: ["error", "asc"] */

import BaseModel from "./BaseModel";

class PaymentPreference extends BaseModel {
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
};

/**
 * Enums for the Application's `payment_preference.payment_method` field
 * @enum {string}
 */
export const PaymentPreferenceMethod = {
  ach: "Elec Funds Transfer",
  check: "Check",
};

export default PaymentPreference;
