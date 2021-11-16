import EmployeesApi, { EmployeeSearchRequest } from "../api/EmployeesApi";

import { AppErrorsLogic } from "./useAppErrorsLogic";
import Employee from "../models/Employee";
import { PortalFlow } from "./usePortalFlow";
import { useState } from "react";

interface Props {
  appErrorsLogic: AppErrorsLogic;
  portalFlow: PortalFlow;
}

const useEmployeesLogic = ({ appErrorsLogic }: Props) => {
  const employeesApi = new EmployeesApi();
  const [employee, setEmployee] = useState<Employee | null>(null);

  /**
   * Search for employee
   */
  const search = async (
    data: EmployeeSearchRequest
  ): Promise<Employee | null> => {
    appErrorsLogic.clearErrors();

    let employee: Employee;
    try {
      employee = await employeesApi.search(data);
      setEmployee(employee);
    } catch (error) {
      appErrorsLogic.catchError(error);
      return null;
    }

    return employee;
  };
  return {
    employee,
    search,
  };
};

export default useEmployeesLogic;
export type EmployeesLogic = ReturnType<typeof useEmployeesLogic>;
