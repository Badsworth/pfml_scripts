import BaseApi from "./BaseApi";
import { Employee } from "../models/User";
import routes from "../routes";

/**
 * @typedef {object} EmployeesAPISingleResult
 * @property {Employee} [reporting_units] - If the request succeeded, this will contain employee's reporting units.
 */

export default class EmployeesApi extends BaseApi {
  get basePath() {
    return routes.api.employees;
  }

  get i18nPrefix() {
    return "employees";
  }

  /**
   * Search
   *
   * @param {object} postData - POST data (SSN/ITIN, name)
   * @returns {Promise}
   */
  search = async (postData) => {
    const { data } = await this.request("POST", "search", postData);
    return new Employee(data);
  };

  /**
   * Determine whether the employee's employer services org units
   * 
   * @param {string} employer_fein
   * @returns {Promise}
   */
   employerHasOrgUnits = async (employer_fein) => {
    const { data } = await this.request(
      "GET",
      "employer-organization-unit-status/"+employer_fein,
    );
    return data.services_org_units;
  }
}
