import { Department } from "src/pages/applications/department";
import { EmployeeOrganizationUnit } from "src/models/Employee";
import { MockBenefitsApplicationBuilder } from "tests/test-utils";
import React from "react";
import User from "src/models/User";
import faker from "faker";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Applications/Department",
  component: Department,
};

const appLogicOptions = (organization_units: EmployeeOrganizationUnit[]) => ({
  employees: {
    search: () =>
      Promise.resolve({
        ...employee,
        organization_units,
      }),
  },
});

const views = () => {
  const Singular = () => (
    <Department
      appLogic={useMockableAppLogic(appLogicOptions(singularDepartmentList))}
      user={user}
      claim={claim}
      query={{}}
    />
  );

  const Short = () => (
    <Department
      appLogic={useMockableAppLogic(appLogicOptions(shortDepartmentList))}
      user={user}
      claim={claim}
      query={{}}
    />
  );

  const Long = () => (
    <Department
      appLogic={useMockableAppLogic(appLogicOptions(longDepartmentList))}
      user={user}
      claim={claim}
      query={{}}
    />
  );

  return {
    Singular,
    Short,
    Long,
  };
};

export const { Singular, Short, Long } = views();

// Mock data
const singularDepartmentList: EmployeeOrganizationUnit[] = [
  {
    organization_unit_id: "dep-1",
    fineos_id: "f-dep-1",
    name: "Department One",
    employer_id: "123456789",
    linked: true,
  },
  {
    organization_unit_id: "dep-2",
    fineos_id: "f-dep-2",
    name: "Department Two",
    employer_id: "123456789",
    linked: false,
  },
];

const shortDepartmentList: EmployeeOrganizationUnit[] = [
  ...singularDepartmentList,
  {
    organization_unit_id: "dep-3",
    fineos_id: "f-dep-3",
    name: "Department Three",
    employer_id: "123456789",
    linked: true,
  },
];

const longDepartmentList: EmployeeOrganizationUnit[] = [
  ...shortDepartmentList,
  {
    organization_unit_id: "dep-4",
    fineos_id: "f-dep-4",
    name: "Department Four",
    employer_id: "123456789",
    linked: true,
  },
  {
    organization_unit_id: "dep-5",
    fineos_id: "f-dep-5",
    name: "Department Five",
    employer_id: "123456789",
    linked: true,
  },
  {
    organization_unit_id: "dep-6",
    fineos_id: "f-dep-6",
    name: "Department Six",
    employer_id: "123456789",
    linked: true,
  },
  {
    organization_unit_id: "dep-7",
    fineos_id: "f-dep-7",
    name: "Department Seven",
    employer_id: "123456789",
    linked: true,
  },
];

const user = new User({
  email_address: faker.internet.email(faker.name.findName()),
});

const claim = new MockBenefitsApplicationBuilder()
  .verifiedId()
  .employed()
  .create();

const employee = {
  employee_id: faker.datatype.uuid(),
  tax_identifier_last4: null,
  first_name: null,
  middle_name: null,
  last_name: null,
  other_name: null,
  email_address: null,
  phone_number: null,
  organization_units: [],
};
