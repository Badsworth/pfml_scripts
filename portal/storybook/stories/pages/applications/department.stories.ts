import { MockBenefitsApplicationBuilder } from "lib/mock-helpers/mock-model-builder";
import OrganizationUnit from "src/models/OrganizationUnit";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

// Mock data
const employerOrgUnitList: OrganizationUnit[] = [
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

const singularDepartmentList = [employerOrgUnitList[0]];

const longDepartmentList = [
  employerOrgUnitList[0],
  employerOrgUnitList[1],
  employerOrgUnitList[2],
  employerOrgUnitList[3],
  employerOrgUnitList[4],
  employerOrgUnitList[5],
];

// Helper
const claimWithUnits = (
  employeeDepartmentList: OrganizationUnit[],
  employerDepartmentList?: OrganizationUnit[]
) =>
  new MockBenefitsApplicationBuilder()
    .verifiedId()
    .employed()
    .employeeOrganizationUnits(employeeDepartmentList)
    .employerOrganizationUnits(employerDepartmentList || employerOrgUnitList)
    .create();

const mockClaims = {
  Singular: claimWithUnits(singularDepartmentList),
  SingularOnlyWorkarounds: claimWithUnits(
    singularDepartmentList,
    singularDepartmentList
  ),
  Long: claimWithUnits(longDepartmentList),
};

const { config, DefaultStory } = generateClaimPageStory(
  "department",
  mockClaims
);

export default config;
export const Default = DefaultStory;
