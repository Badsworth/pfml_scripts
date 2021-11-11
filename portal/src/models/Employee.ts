/* eslint sort-keys: ["error", "asc"] */

export interface OrganizationUnit {
  organization_unit_id: string;
  fineos_id: string | null;
  name: string;
  employer_id: string | null;
}

export interface EmployeeOrganizationUnit extends OrganizationUnit {
  linked: boolean;
}

interface Employee {
  employee_id: string;
  tax_identifier_last4: string | null;
  first_name: string | null;
  middle_name: string | null;
  last_name: string | null;
  other_name: string | null;
  email_address: string | null;
  phone_number: string | null;
  organization_units?: EmployeeOrganizationUnit[];
}

export default Employee;
