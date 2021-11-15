import { MockBenefitsApplicationBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  "Bonding (Fixed)": new MockBenefitsApplicationBuilder()
    .fixedWorkPattern()
    .bondingBirthLeaveReason()
    .create(),
  "Bonding (Variable)": new MockBenefitsApplicationBuilder()
    .variableWorkPattern()
    .bondingBirthLeaveReason()
    .create(),
  "Caring (Fixed)": new MockBenefitsApplicationBuilder()
    .fixedWorkPattern()
    .caringLeaveReason()
    .create(),
  "Caring (Variable)": new MockBenefitsApplicationBuilder()
    .variableWorkPattern()
    .caringLeaveReason()
    .create(),
  "Medical (Fixed)": new MockBenefitsApplicationBuilder()
    .fixedWorkPattern()
    .medicalLeaveReason()
    .create(),
  "Medical (Variable)": new MockBenefitsApplicationBuilder()
    .variableWorkPattern()
    .medicalLeaveReason()
    .create(),
  "Medical leave for pregnancy or birth (Fixed)":
    new MockBenefitsApplicationBuilder()
      .fixedWorkPattern()
      .pregnancyLeaveReason()
      .create(),
  "Medical leave for pregnancy or birth (Variable)":
    new MockBenefitsApplicationBuilder()
      .variableWorkPattern()
      .pregnancyLeaveReason()
      .create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "reduced-leave-schedule",
  mockClaims
);
export default config;
export const Default = DefaultStory;
