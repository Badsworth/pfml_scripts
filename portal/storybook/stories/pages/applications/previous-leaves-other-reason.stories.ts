import { MockBenefitsApplicationBuilder } from "tests/test-utils/mock-model-builder";
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
};

const { config, DefaultStory } = generateClaimPageStory(
  "previous-leaves-other-reason",
  mockClaims
);
export default config;
export const Default = DefaultStory;
