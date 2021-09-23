/* eslint sort-keys: ["error", "asc"] */
import BaseModel from "./BaseModel";

class User extends BaseModel {
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
    return this.user_leave_administrators.some(
      (employer) => employer && this.isVerifiableEmployer(employer)
    );
  }

  /**
   * Returns an unverifiable employer by employer id
   * @param {string} employerId
   * @returns {UserLeaveAdministrator}
   */
  getUnverifiableEmployerById(employerId) {
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
    return this.user_leave_administrators.find((employer) => {
      return (
        employerId === employer.employer_id &&
        this.isVerifiableEmployer(employer)
      );
    });
  }

  /**
   * Returns list of verified employers
   * @returns {UserLeaveAdministrator[]}
   */
  get verifiedEmployers() {
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
    return this.user_leave_administrators.some(
      (employer) =>
        employerId === employer.employer_id && employer.has_fineos_registration
    );
  }
}

export class UserRole extends BaseModel {
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
