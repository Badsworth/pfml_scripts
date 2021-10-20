import EmployeesApi from "../api/EmployeesApi";
import { useMemo } from "react";

const useEmployeesLogic = ({ appErrorsLogic, portalFlow }) => {
  const employeesApi = useMemo(() => new EmployeesApi(), []);

  /**
   * Search for employee
   *
   * @param {object} data - First, middle, last name, tax_identifier_last4
   * @returns {object} Employee
   */
  const search = async (data) => {
    appErrorsLogic.clearErrors();

    try {
      return await employeesApi.search(data);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  const employerHasOrgUnits = async (employer_fein) => {
    try {
      return await employeesApi.employerHasOrgUnits(employer_fein)
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  }

  return {
    search,
    employerHasOrgUnits,
  };
};

export default useEmployeesLogic;
