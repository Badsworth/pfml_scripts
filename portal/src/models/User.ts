/* eslint sort-keys: ["error", "asc"] */

class User {
  auth_id: string;
  consented_to_data_sharing: boolean;
  email_address: string;
  roles: UserRole[] = [];
  user_id: string;
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
    return this.user_leave_administrators.some(
      (employer) => employer && this.isVerifiableEmployer(employer)
    );
  }

  /**
   * Returns an unverifiable employer by employer id
   */
  getUnverifiableEmployerById(employerId: string): UserLeaveAdministrator {
    return this.user_leave_administrators.find((employer) => {
      return (
        employerId === employer.employer_id &&
        this.isUnverifiableEmployer(employer)
      );
    });
  }

  /**
   * Returns a verifiable employer by employer id
   */
  getVerifiableEmployerById(employerId: string): UserLeaveAdministrator {
    return this.user_leave_administrators.find((employer) => {
      return (
        employerId === employer.employer_id &&
        this.isVerifiableEmployer(employer)
      );
    });
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
   * Determines whether an employer is NOT verifiable (unverified and lacks verification data)
   */
  isUnverifiableEmployer(employer: UserLeaveAdministrator): boolean {
    return !employer.verified && !employer.has_verification_data;
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
  role_description:
    | typeof RoleDescription[keyof typeof RoleDescription]
    | null = null;

  role_id: string | null = null;

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
  employer_dba: string | null = null;
  employer_fein: string | null = null;
  employer_id: string | null = null;
  has_fineos_registration: boolean | null = null;
  has_verification_data: boolean | null = null;
  verified: boolean | null = null;

  constructor(attrs: Partial<UserLeaveAdministrator>) {
    Object.assign(this, attrs);
  }
}

export default User;
