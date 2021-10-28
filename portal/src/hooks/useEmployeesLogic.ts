import { Employee } from "../models/User";
import EmployeesApi, { EmployeeSearchRequest } from "../api/EmployeesApi";
import { useMemo } from "react";


const useEmployeesLogic = ({ appErrorsLogic, portalFlow }) => {
  const employeesApi = useMemo(() => new EmployeesApi(), []);

  /**
   * Search for employee
   */
  const search = async (data: EmployeeSearchRequest, applicationId: string): Promise<Employee> => {
    appErrorsLogic.clearErrors();

    try {
      const employee = await employeesApi.search(data);
      if (!employee.organization_units.length) {
        portalFlow.goToNextPage({}, { claim_id: applicationId });
      }
      return employee
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };
  return {
    search,
  };
};

export default useEmployeesLogic;
