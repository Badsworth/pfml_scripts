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
   * @returns {Promise} Employee: Promise<Employee>
   */
  search = async (postData) => {
    const { data } = await this.request<Employee>("POST", "search", postData);
    console.log({postData}, data)
    return data;
  };
}
