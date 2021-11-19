import { MockBenefitsApplicationBuilder } from "tests/test-utils";
import OrganizationUnit from "src/models/OrganizationUnit";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

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

const claimWithUnits = (employeeDepartmentList: OrganizationUnit[]) =>
  new MockBenefitsApplicationBuilder()
    .verifiedId()
    .employed()
    .employeeOrganizationUnits(employeeDepartmentList)
    .employerOrganizationUnits(employerDepartmentList)
    .create();

const mockClaims = {
  empty: claimWithUnits(longDepartmentList),
  "Singular List": claimWithUnits(singularDepartmentList),
  "Short List": claimWithUnits(shortDepartmentList),
  "Long List": claimWithUnits(longDepartmentList),
};

const { config, DefaultStory } = generateClaimPageStory(
  "department",
  mockClaims
);
export default config;
export const Default = DefaultStory;
