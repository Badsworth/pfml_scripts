/* eslint sort-keys: ["error", "asc"] */

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

type BankAccountTypeType = typeof BankAccountType[keyof typeof BankAccountType];
type PaymentPreferenceMethodType =
  typeof PaymentPreferenceMethod[keyof typeof PaymentPreferenceMethod];

class PaymentPreference {
  account_number: string | null = null;
  bank_account_type: BankAccountTypeType | null = null;
  payment_method: PaymentPreferenceMethodType | null = null;
  routing_number: string | null = null;

  constructor(attrs: PaymentPreference) {
    Object.assign(this, attrs);
  }
}

export default PaymentPreference;
