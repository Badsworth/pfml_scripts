import { ValuesOf } from "../../types/common";

/* eslint sort-keys: ["error", "asc"] */
export const PhoneType = {
  cell: "Cell",
  phone: "Phone",
} as const;

export const MFAPreference = {
  optOut: "Opt Out",
  sms: "SMS",
} as const;

class User {
  auth_id: string;
  consented_to_data_sharing: boolean;
  email_address: string;
  roles: UserRole[] = [];
  user_id: string;
  mfa_phone_number: {
    int_code: string | null;
    phone_number: string | null;
    phone_type: ValuesOf<typeof PhoneType> | null;
  } | null = null;

  mfa_delivery_preference: ValuesOf<typeof MFAPreference> | null = null;

  user_leave_administrators: UserLeaveAdministrator[] = [];

  constructor(attrs: Partial<User>) {
    Object.assign(this, attrs);
  }

  get hasEmployerRole() {
    return this.roles.some(
      (userRole) => userRole.role_description === RoleDescription.employer
    );
  }

  /**
   * Determines whether user_leave_administrators has only unverified employers
   */
  get hasOnlyUnverifiedEmployers(): boolean {
    return this.verifiedEmployers.length === 0;
  }

  /**
   * Determines whether user_leave_administrators has a verifiable employer
   */
  get hasVerifiableEmployer(): boolean {
    return this.user_leave_administrators.some((employer) =>
      this.isVerifiableEmployer(employer)
    );
  }

  /**
   * Returns list of verified employers
   */
  get verifiedEmployers(): UserLeaveAdministrator[] {
    return this.user_leave_administrators.filter(
      (employer) => employer.verified === true
    );
  }

  /**
   * Determines whether an employer is verifiable (unverified and has verification data)
   */
  isVerifiableEmployer(employer: UserLeaveAdministrator): boolean {
    return !employer.verified && employer.has_verification_data;
  }

  /**
   * Determines whether an employer is registered in FINEOS
   */
  isEmployerIdRegisteredInFineos(employerId: string | null): boolean {
    return this.user_leave_administrators.some(
      (employer) =>
        employerId === employer.employer_id && employer.has_fineos_registration
    );
  }
}

export class UserRole {
  role_description: ValuesOf<typeof RoleDescription>;
  role_id: number;

  constructor(attrs: Partial<UserRole>) {
    Object.assign(this, attrs);
  }
}

/**
 * Enums for UserRole's `role_description` field
 * @enum {string}
 */
export const RoleDescription = {
  claimant: "Claimant",
  employer: "Employer",
} as const;

export class UserLeaveAdministrator {
  employer_dba: string | null;
  employer_fein: string;
  employer_id: string;
  has_fineos_registration: boolean;
  has_verification_data: boolean;
  verified: boolean;

  constructor(attrs: Partial<UserLeaveAdministrator>) {
    Object.assign(this, attrs);
  }
}

export default User;
