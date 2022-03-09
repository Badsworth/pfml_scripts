import { MockBenefitsApplicationBuilder } from "lib/mock-helpers/mock-model-builder";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const leavePeriodAttrs = {
  start_date: "2022-03-07",
};

const mockClaims = {
  continuous: new MockBenefitsApplicationBuilder()
    .employed()
    .continuous(leavePeriodAttrs)
    .create(),
  intermittent: new MockBenefitsApplicationBuilder()
    .employed()
    .intermittent(leavePeriodAttrs)
    .create(),
  caring: new MockBenefitsApplicationBuilder()
    .employed()
    .caringLeaveReason()
    .continuous(leavePeriodAttrs)
    .create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "previous-leaves-same-reason-details",
  mockClaims
);
export default config;
export const Default = DefaultStory;
