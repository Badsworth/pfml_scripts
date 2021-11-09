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
  // @ts-expect-error ts-migrate(2345) FIXME: Argument of type '{ continuous: BenefitsApplicatio... Remove this comment to see the full error message
  mockClaims
);
export default config;
export const Default = DefaultStory;
