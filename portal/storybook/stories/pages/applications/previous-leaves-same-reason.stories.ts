import { MockBenefitsApplicationBuilder } from "lib/mock-helpers/mock-model-builder";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const leavePeriodAttrs = {
  start_date: "2021-03-07",
};

const mockClaims = {
  continuous: new MockBenefitsApplicationBuilder()
    .continuous(leavePeriodAttrs)
    .create(),
  intermittent: new MockBenefitsApplicationBuilder()
    .intermittent(leavePeriodAttrs)
    .create(),
  caring: new MockBenefitsApplicationBuilder()
    .caringLeaveReason()
    .continuous()
    .create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "previous-leaves-same-reason",
  mockClaims
);
export default config;
export const Default = DefaultStory;
