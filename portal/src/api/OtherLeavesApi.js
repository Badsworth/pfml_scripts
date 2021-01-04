import BaseApi from "./BaseApi";
import routes from "../routes";

export default class OtherLeavesApi extends BaseApi {
  get basePath() {
    return routes.api.claims;
  }

  get i18nPrefix() {
    return "otherLeaves";
  }

  /**
   * Deletes an employer benefit
   * @param {string} applicationId ID of the Claim
   * @param {string} employerBenefitId ID of the employer benefit
   * @throws {Error} if the request fails
   */
  removeEmployerBenefit = async (applicationId, employerBenefitId) => {
    await this.request(
      "DELETE",
      `${applicationId}/employer_benefits/${employerBenefitId}`
    );
  };

  /**
   * Deletes an other income
   * @param {string} applicationId ID of the Claim
   * @param {string} otherIncomeId ID of the other income
   * @throws {Error} if the request fails
   */
  removeOtherIncome = async (applicationId, otherIncomeId) => {
    await this.request(
      "DELETE",
      `${applicationId}/other_incomes/${otherIncomeId}`
    );
  };

  /**
   * Deletes an previous leave
   * @param {string} applicationId ID of the Claim
   * @param {string} previousLeaveId ID of the previous leave
   * @throws {Error} if the request fails
   */
  removePreviousLeave = async (applicationId, previousLeaveId) => {
    await this.request(
      "DELETE",
      `${applicationId}/previous_leaves/${previousLeaveId}`
    );
  };
}
