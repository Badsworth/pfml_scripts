import BaseApi from "./BaseApi";
import EmployerClaim from "../models/EmployerClaim";
import routes from "../routes";

/**
 * @typedef {object} EmployersAPISingleResult
 * @property {number} status - Status code
 * @property {boolean} success - Returns true if 2xx status code
 * @property {EmployerClaim} [claim] - If the request succeeded, this will contain a claim
 */

export default class EmployersApi extends BaseApi {
  get basePath() {
    return routes.api.employers;
  }

  get i18nPrefix() {
    return "employers";
  }

  /**
   * Retrieve a claim
   *
   * @param {string} absenceId - FINEOS absence id
   * @returns {Promise<EmployersAPISingleResult>}
   */
  getClaim = async (absenceId) => {
    const { data, success, status } = await this.request(
      "GET",
      `claims/${absenceId}/review`
    );

    return {
      claim: success ? new EmployerClaim(data) : null,
      status,
      success,
    };
  };

  /**
   * Submit an employer claim review
   *
   * @param {string} absenceId - FINEOS absence id
   * @param {object} patchData - PATCH data of amendment and comment fields
   * @returns {Promise<EmployersAPISingleResult>}
   */
  submitClaimReview = async (absenceId, patchData) => {
    const { status, success } = await this.request(
      "PATCH",
      `claims/${absenceId}/review`,
      patchData
    );

    return {
      claim: null,
      status,
      success,
    };
  };
}
