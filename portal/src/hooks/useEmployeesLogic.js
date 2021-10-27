import EmployeesApi from "../api/EmployeesApi.ts";
import { useMemo } from "react";

const useEmployeesLogic = ({ appErrorsLogic, portalFlow }) => {
  const employeesApi = useMemo(() => new EmployeesApi(), []);

  /**
   * Search for employee
   *
   * @param {object} data - First, middle, last name, tax_identifier_last4
   * @returns {object} Employee
   */
  const search = async (data, applicationId) => {
    appErrorsLogic.clearErrors();

    try {
      const employee = await employeesApi.search(data);
      if (!employee.organization_units.length) {
        portalFlow.goToNextPage({}, { claim_id: applicationId });
      }
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };
  return {
    search,
  };
};

export default useEmployeesLogic;
