/* eslint sort-keys: ["error", "asc"] */
import BaseModel from "./BaseModel";

class User extends BaseModel {
  // @ts-expect-error ts-migrate(2416) FIXME: Property 'defaults' in type 'User' is not assignab... Remove this comment to see the full error message
  get defaults() {
    return {
      auth_id: null,
      consented_to_data_sharing: null,
      email_address: null,
      roles: [], // array of UserRole
      status: null,
      user_id: null,
      user_leave_administrators: [], // array of UserLeaveAdministrator
    };
  }

  get hasEmployerRole() {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'roles' does not exist on type 'User'.
    return this.roles.some(
      (userRole) => userRole.role_description === RoleDescription.employer
    );
  }

  /**
   * Determines whether user_leave_administrators has only unverified employers
   * @returns {boolean}
   */
  get hasOnlyUnverifiedEmployers() {
    return this.verifiedEmployers.length === 0;
  }

  /**
   * Determines whether user_leave_administrators has a verifiable employer
   * @returns {boolean}
   */
  get hasVerifiableEmployer() {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'user_leave_administrators' does not exis... Remove this comment to see the full error message
    return this.user_leave_administrators.some(
      (employer) => employer && this.isVerifiableEmployer(employer)
    );
  }

  /**
   * Determines whether user_leave_administrators has at least one verified employer NOT registered in FINEOS
   * @returns {boolean}
   */
  get hasVerifiedEmployerNotRegisteredInFineos() {
    return !!this.verifiedEmployersNotRegisteredInFineos.length;
  }

  /**
   * Returns an unverifiable employer by employer id
   * @param {string} employerId
   * @returns {UserLeaveAdministrator}
   */
  getUnverifiableEmployerById(employerId) {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'user_leave_administrators' does not exis... Remove this comment to see the full error message
    return this.user_leave_administrators.find((employer) => {
      return (
        employerId === employer.employer_id &&
        this.isUnverifiableEmployer(employer)
      );
    });
  }

  /**
   * Returns a verifiable employer by employer id
   * @param {string} employerId
   * @returns {UserLeaveAdministrator}
   */
  getVerifiableEmployerById(employerId) {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'user_leave_administrators' does not exis... Remove this comment to see the full error message
    return this.user_leave_administrators.find((employer) => {
      return (
        employerId === employer.employer_id &&
        this.isVerifiableEmployer(employer)
      );
    });
  }

  /**
   * Returns list of verified employers that are not registered in FINEOS
   * @returns {UserLeaveAdministrator[]}
   */
  get verifiedEmployersNotRegisteredInFineos() {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'user_leave_administrators' does not exis... Remove this comment to see the full error message
    return this.user_leave_administrators.filter(
      (employer) =>
        employer.has_fineos_registration === false && employer.verified === true
    );
  }

  /**
   * Returns list of verified employers
   * @returns {UserLeaveAdministrator[]}
   */
  get verifiedEmployers() {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'user_leave_administrators' does not exis... Remove this comment to see the full error message
    return this.user_leave_administrators.filter(
      (employer) => employer.verified === true
    );
  }

  /**
   * Determines whether an employer is NOT verifiable (unverified and lacks verification data)
   * @param {UserLeaveAdministrator} employer
   * @returns {boolean}
   */
  isUnverifiableEmployer(employer) {
    return !employer.verified && !employer.has_verification_data;
  }

  /**
   * Determines whether an employer is verifiable (unverified and has verification data)
   * @param {UserLeaveAdministrator} employer
   * @returns {boolean}
   */
  isVerifiableEmployer(employer) {
    return !employer.verified && employer.has_verification_data;
  }

  /**
   * Determines whether an employer is registered in FINEOS
   * @param {string} employerId
   * @returns {boolean}
   */
  isEmployerIdRegisteredInFineos(employerId) {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'user_leave_administrators' does not exis... Remove this comment to see the full error message
    return this.user_leave_administrators.some(
      (employer) =>
        employerId === employer.employer_id && employer.has_fineos_registration
    );
  }
}

export class UserRole extends BaseModel {
  // @ts-expect-error ts-migrate(2416) FIXME: Property 'defaults' in type 'UserRole' is not assi... Remove this comment to see the full error message
  get defaults() {
    return {
      role_description: null,
      role_id: null,
    };
  }
}

/**
 * Enums for UserRole's `role_description` field
 * @enum {string}
 */
export const RoleDescription = {
  claimant: "Claimant",
  employer: "Employer",
};

export class UserLeaveAdministrator extends BaseModel {
  // @ts-expect-error ts-migrate(2416) FIXME: Property 'defaults' in type 'UserLeaveAdministrato... Remove this comment to see the full error message
  get defaults() {
    return {
      employer_dba: null,
      employer_fein: null,
      employer_id: null,
      has_fineos_registration: null,
      has_verification_data: null,
      verified: null,
    };
  }
}

export default User;
