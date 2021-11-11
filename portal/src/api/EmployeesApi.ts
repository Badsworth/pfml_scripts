import BaseApi, { JSONRequestBody } from "./BaseApi";
import { Employee } from "../models/User";
import routes from "../routes";

export interface EmployeeSearchRequest extends JSONRequestBody {
  first_name: string;
  last_name: string;
  middle_name?: string;
  tax_identifier_last4: string;
  employer_fein?: string;
}

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
  search = async (postData: EmployeeSearchRequest): Promise<Employee> => {
    const { data } = await this.request<Employee>("POST", "search", postData);
    return data;
  };
}
