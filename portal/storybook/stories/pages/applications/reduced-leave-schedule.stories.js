import { MockClaimBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  "Bonding (Fixed)": new MockClaimBuilder()
    .fixedWorkPattern()
    .bondingBirthLeaveReason()
    .create(),
  "Bonding (Variable)": new MockClaimBuilder()
    .variableWorkPattern()
    .bondingBirthLeaveReason()
    .create(),
  "Medical (Fixed)": new MockClaimBuilder()
    .fixedWorkPattern()
    .medicalLeaveReason()
    .create(),
  "Medical (Variable)": new MockClaimBuilder()
    .variableWorkPattern()
    .medicalLeaveReason()
    .create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "reduced-leave-schedule",
  mockClaims
);
export default config;
export const Default = DefaultStory;
