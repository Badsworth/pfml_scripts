import { MockBenefitsApplicationBuilder } from "tests/test-utils/mock-model-builder";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  "Medical leave": new MockBenefitsApplicationBuilder()
    .medicalLeaveReason()
    .create(),
  "Medical leave for pregnancy or birth": new MockBenefitsApplicationBuilder()
    .pregnancyLeaveReason()
    .create(),
  "Bonding: newborn": new MockBenefitsApplicationBuilder()
    .bondingBirthLeaveReason()
    .create(),
  "Bonding: adoption/foster": new MockBenefitsApplicationBuilder()
    .bondingAdoptionLeaveReason()
    .create(),
  "Caring leave": new MockBenefitsApplicationBuilder()
    .caringLeaveReason()
    .create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "upload-docs-options",
  mockClaims
);
export default config;
export const Default = DefaultStory;
