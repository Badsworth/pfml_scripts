import BaseApi from "./BaseApi";
import routes from "../routes";

/**
 * @typedef {object} EmployersAPISingleResult
 * @property {boolean} success Whether or not the request was successful
 * @property {number} status Status code
 */

export default class EmployersApi extends BaseApi {
  get basePath() {
    return routes.api.employers;
  }

  get i18nPrefix() {
    return "employers";
  }

  /**
   * Submit an employer claim review
   *
   * @param {string} absenceId - FINEOS absence id
   * @param {object} patchData - PATCH data of amendment and comment fields
   * @returns {Promise<EmployersAPISingleResult>}
   */
  submitClaimReview = async (absenceId, patchData) => {
    const { success, status } = await this.request(
      "PATCH",
      `claims/${absenceId}/review`,
      patchData
    );

    return Promise.resolve({
      success,
      status,
    });
  };
}
