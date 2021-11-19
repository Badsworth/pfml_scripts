import { Department } from "src/pages/applications/department";
import { MockBenefitsApplicationBuilder } from "tests/test-utils";
import OrganizationUnit from "src/models/OrganizationUnit";
import { Props } from "storybook/types";
import React from "react";
import User from "src/models/User";
import faker from "faker";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

// Mock data
const employerDepartmentList = [
  {
    organization_unit_id: "dep-1",
    name: "Department One",
  },
  {
    organization_unit_id: "dep-2",
    name: "Department Two",
  },
  {
    organization_unit_id: "dep-3",
    name: "Department Three",
  },
  {
    organization_unit_id: "dep-4",
    name: "Department Four",
  },
  {
    organization_unit_id: "dep-5",
    name: "Department Five",
  },
  {
    organization_unit_id: "dep-6",
    name: "Department Six",
  },
  {
    organization_unit_id: "dep-7",
    name: "Department Seven",
  },
  {
    organization_unit_id: "dep-8",
    name: "Department Eight",
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

const scenarios = {
  "Singular List": {
    claim: claimWithUnits(singularDepartmentList),
  },
  "Short List": {
    claim: claimWithUnits(shortDepartmentList),
  },
  "Long List": {
    claim: claimWithUnits(longDepartmentList),
  },
};

export default {
  title: "Pages/Applications/Department",
  component: Department,
  argTypes: {
    scenario: {
      defaultValue: Object.keys(scenarios)[0],
      control: {
        type: "radio",
        options: Object.keys(scenarios),
      },
    },
  },
};

export const DefaultStory = (
  args: Props<typeof Department> & { scenario: keyof typeof scenarios }
) => {
  const { claim } = scenarios[args.scenario];

  const appLogic = useMockableAppLogic();

  return <Department appLogic={appLogic} user={user} claim={claim} />;
};
