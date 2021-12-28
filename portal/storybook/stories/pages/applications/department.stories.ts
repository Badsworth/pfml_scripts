import { MockBenefitsApplicationBuilder } from "lib/mock-helpers/mock-model-builder";
import OrganizationUnit from "src/models/OrganizationUnit";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";
import { updateCookieWithFlag } from "src/services/featureFlags";

// Mock data
const employerDepartmentList: OrganizationUnit[] = [
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

const longDepartmentList = [
  employerDepartmentList[0],
  employerDepartmentList[1],
  employerDepartmentList[2],
  employerDepartmentList[3],
  employerDepartmentList[4],
  employerDepartmentList[5],
];

// Helper
const claimWithUnits = (employeeDepartmentList: OrganizationUnit[]) =>
  new MockBenefitsApplicationBuilder()
    .verifiedId()
    .employed()
    .employeeOrganizationUnits(employeeDepartmentList)
    .employerOrganizationUnits(employerDepartmentList)
    .create();

const mockClaims = {
  Long: claimWithUnits(longDepartmentList),
};

// Workaround to pass render stories test
// The department page is currently behind a feature flag
// and causes the stories test to fail due to empty story component
updateCookieWithFlag("claimantShowOrganizationUnits", "true");

const { config, DefaultStory } = generateClaimPageStory(
  "department",
  mockClaims
);

export default config;
export const Default = DefaultStory;
