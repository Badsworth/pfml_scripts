import EmployeesApi, { EmployeeSearchRequest } from "../api/EmployeesApi";
import { AppErrorsLogic } from "./useAppErrorsLogic";
import { Employee } from "../models/User";
import { PortalFlow } from "./usePortalFlow";
import { useMemo } from "react";

interface Props {
  appErrorsLogic: AppErrorsLogic;
  portalFlow: PortalFlow;
}

const useEmployeesLogic = ({ appErrorsLogic, portalFlow }: Props) => {
  const employeesApi = useMemo(() => new EmployeesApi(), []);

  /**
   * Search for employee
   */
  const search = async (
    data: EmployeeSearchRequest,
    applicationId: string
  ): Promise<Employee | null> => {
    appErrorsLogic.clearErrors();

    let employee: Employee;
    try {
      employee = await employeesApi.search(data);
    } catch (error) {
      appErrorsLogic.catchError(error);
      return null;
    }

    if (typeof employee.organization_units !== "undefined") {
      if (employee.organization_units.length === 0) {
        portalFlow.goToNextPage({}, { claim_id: applicationId });
      }
    }
    return employee;
  };
  return {
    search,
  };
};

export default useEmployeesLogic;
