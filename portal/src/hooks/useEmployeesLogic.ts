import EmployeesApi, { EmployeeSearchRequest } from "../api/EmployeesApi";
import { AppErrorsLogic } from "./useAppErrorsLogic";
import { Employee } from "../models/User";
import { PortalFlow } from "./usePortalFlow";

interface Props {
  appErrorsLogic: AppErrorsLogic;
  portalFlow: PortalFlow;
}

const useEmployeesLogic = ({ appErrorsLogic }: Props) => {
  const employeesApi = new EmployeesApi();

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
    } catch (error) {
      appErrorsLogic.catchError(error);
      return null;
    }

    return employee;
  };
  return {
    search,
  };
};

export default useEmployeesLogic;
