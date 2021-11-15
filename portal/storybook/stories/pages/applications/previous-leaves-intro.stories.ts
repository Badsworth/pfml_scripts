import { MockBenefitsApplicationBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const leavePeriodAttrs = {
  start_date: "2021-03-07",
};

const mockClaims = {
  continuous: new MockBenefitsApplicationBuilder()
    .employed()
    .continuous(leavePeriodAttrs)
    .create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "previous-leaves-intro",
  mockClaims
);
export default config;
export const Default = DefaultStory;
