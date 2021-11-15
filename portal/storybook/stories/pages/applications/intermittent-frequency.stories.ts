import { MockBenefitsApplicationBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  bonding: new MockBenefitsApplicationBuilder()
    .bondingBirthLeaveReason()
    .create(),
  caring: new MockBenefitsApplicationBuilder().caringLeaveReason().create(),
  medical: new MockBenefitsApplicationBuilder().medicalLeaveReason().create(),
  "Medical leave for pregnancy or birth": new MockBenefitsApplicationBuilder()
    .pregnancyLeaveReason()
    .create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "intermittent-frequency",
  mockClaims
);
export default config;
export const Default = DefaultStory;
