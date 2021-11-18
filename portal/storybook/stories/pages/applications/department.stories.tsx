import { Department } from "src/pages/applications/department";
import { MockBenefitsApplicationBuilder } from "tests/test-utils";
import OrganizationUnit from "src/models/OrganizationUnit";
import React from "react";
import User from "src/models/User";
import faker from "faker";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Applications/Department",
  component: Department,
};

const views = () => {
  const Singular = () => {
    const appLogic = useMockableAppLogic();
    return (
      <Department
        appLogic={appLogic}
        user={user}
        claim={claimWithUnits(singularDepartmentList)}
      />
    );
  };

  const Short = () => {
    const appLogic = useMockableAppLogic();
    return (
      <Department
        appLogic={appLogic}
        user={user}
        claim={claimWithUnits(shortDepartmentList)}
      />
    );
  };

  const Long = () => {
    const appLogic = useMockableAppLogic();
    return (
      <Department
        appLogic={appLogic}
        user={user}
        claim={claimWithUnits(longDepartmentList)}
      />
    );
  };

  return {
    Singular,
    Short,
    Long,
  };
};

export const { Singular, Short, Long } = views();

// Mock data
const employerDepartmentList = [
  {
    organization_unit_id: "dep-1",
    fineos_id: "f-dep-1",
    name: "Department One",
    employer_id: "123456789",
  },
  {
    organization_unit_id: "dep-2",
    fineos_id: "f-dep-2",
    name: "Department Two",
    employer_id: "123456789",
  },
  {
    organization_unit_id: "dep-3",
    fineos_id: "f-dep-3",
    name: "Department Three",
    employer_id: "123456789",
  },
  {
    organization_unit_id: "dep-4",
    fineos_id: "f-dep-4",
    name: "Department Four",
    employer_id: "123456789",
  },
  {
    organization_unit_id: "dep-5",
    fineos_id: "f-dep-5",
    name: "Department Five",
    employer_id: "123456789",
  },
  {
    organization_unit_id: "dep-6",
    fineos_id: "f-dep-6",
    name: "Department Six",
    employer_id: "123456789",
  },
  {
    organization_unit_id: "dep-7",
    fineos_id: "f-dep-7",
    name: "Department Seven",
    employer_id: "123456789",
  },
  {
    organization_unit_id: "dep-8",
    fineos_id: "f-dep-8",
    name: "Department Eight",
    employer_id: "123456789",
  },
];

const singularDepartmentList: OrganizationUnit[] = [employerDepartmentList[0]];
const shortDepartmentList: OrganizationUnit[] = [
  employerDepartmentList[0],
  employerDepartmentList[1],
];
const longDepartmentList: OrganizationUnit[] = [
  employerDepartmentList[0],
  employerDepartmentList[1],
  employerDepartmentList[2],
  employerDepartmentList[3],
  employerDepartmentList[4],
  employerDepartmentList[5],
];

const user = new User({
  email_address: faker.internet.email(faker.name.findName()),
});

const claimWithUnits = (employeeDepartmentList: OrganizationUnit[]) =>
  new MockBenefitsApplicationBuilder()
    .verifiedId()
    .employed()
    .employeeOrganizationUnits(employeeDepartmentList)
    .employerOrganizationUnits(employerDepartmentList)
    .create();
