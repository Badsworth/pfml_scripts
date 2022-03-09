import { MockBenefitsApplicationBuilder } from "lib/mock-helpers/mock-model-builder";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  Adoption: new MockBenefitsApplicationBuilder()
    .continuous()
    .bondingAdoptionLeaveReason()
    .create(),
  Newborn: new MockBenefitsApplicationBuilder()
    .continuous()
    .bondingBirthLeaveReason()
    .create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "date-of-child",
  mockClaims
);

export default config;
export const Default = DefaultStory;
