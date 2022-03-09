import { MockBenefitsApplicationBuilder } from "lib/mock-helpers/mock-model-builder";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const leavePeriodAttrs = {
  start_date: "2022-01-09",
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
