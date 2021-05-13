import { MockBenefitsApplicationBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  "Medical leave": new MockBenefitsApplicationBuilder()
    .medicalLeaveReason()
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
  "upload-certification",
  mockClaims
);
export default config;
export const Default = DefaultStory;
