import { EmployeeRecord } from "@/simulation/types";

/**
 * Fetch an id'ed employee from the employee.json file.
 * @param id
 */
export async function getEmployee(id: string): Promise<EmployeeRecord> {
  const employees = await import(`${__dirname}/../employee.json`);
  if (id in employees) {
    return employees[id];
  }
  throw new Error(`Unable to find employee ${id} in employees file`);
}
