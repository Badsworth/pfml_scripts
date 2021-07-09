/* eslint-disable jsdoc/require-returns */
import BaseApi from "./BaseApi";
// import BenefitsApplication from "../models/BenefitsApplication";
// import BenefitsApplicationCollection from "../models/BenefitsApplicationCollection";
// import { isFeatureEnabled } from "../services/featureFlags";
import routes from "../routes";

/**
 * @typedef {object} BenefitsApplicationsApiSingleResult
 * @property {BenefitsApplication} [claim] - If the request succeeded, this will contain the created claim
 * @property {{ field: string, message: string, rule: string, type: string }[]} [warnings] - Validation warnings
 */

/**
 * @typedef {object} BenefitsApplicationsApiListResult
 * @property {BenefitsApplicationCollection} [claims] - If the request succeeded, this will contain the created user
 */

export default class DepartmentsApi extends BaseApi {
  get basePath() {
    return routes.api.departments;
  }

  get i18nPrefix() {
    return "departments";
  }

  /**
   * Signal the data entry is complete and application is ready
   * for intake to be marked as complete in the claims processing system.
   *
   * @param {string} application_id
   * @returns {Promise<BenefitsApplicationsApiSingleResult>} The result of the API call
   */
  searchDepartment = async (postData) => {
    // const { data } = await this.request(
    //   "POST",
    //   `/employees/search`,
    //   postData
    // );

    return {
      //departments: new Department(data),
      departments: ["Brenton", "Melqui"],
    };
  };
}
