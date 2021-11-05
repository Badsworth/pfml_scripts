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
  "leave-period-reduced-schedule",
  // @ts-expect-error ts-migrate(2345) FIXME: Argument of type '{ bonding: BenefitsApplication; ... Remove this comment to see the full error message
  mockClaims
);
export default config;
export const Default = DefaultStory;
