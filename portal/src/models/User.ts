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
    return this.user_leave_administrators.some((employer) =>
      this.isVerifiableEmployer(employer)
    );
  }

  /**
   * Returns an unverifiable employer by employer id
   */
  getUnverifiableEmployerById(employerId: string) {
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
  getVerifiableEmployerById(employerId: string) {
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
  role_description: typeof RoleDescription[keyof typeof RoleDescription];
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

export interface OrganizationUnit {
  organization_unit_id: string;
  fineos_id: string | null;
  name: string;
  employer_id: string | null;
}

export interface EmployeeOrganizationUnit extends OrganizationUnit {
  linked: boolean;
}

export class UserLeaveAdministrator {
  employer_dba: string;
  employer_fein: string;
  employer_id: string;
  has_fineos_registration: boolean;
  has_verification_data: boolean;
  verified: boolean;
  organization_units?: OrganizationUnit[];

  constructor(attrs: Partial<UserLeaveAdministrator>) {
    Object.assign(this, attrs);
  }
}

export interface Employee {
  employee_id: string;
  tax_identifier_last4: string | null;
  first_name: string | null;
  middle_name: string | null;
  last_name: string | null;
  other_name: string | null;
  email_address: string | null;
  phone_number: string | null;
  organization_units?: EmployeeOrganizationUnit[];
}

export default User;
