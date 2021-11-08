import { MockBenefitsApplicationBuilder } from "tests/test-utils";
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
  // @ts-expect-error ts-migrate(2345) FIXME: Argument of type '{ "Medical leave": BenefitsAppli... Remove this comment to see the full error message
  mockClaims
);
export default config;
export const Default = DefaultStory;
