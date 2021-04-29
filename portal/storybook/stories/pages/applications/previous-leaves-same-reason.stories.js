import { MockClaimBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const leavePeriodAttrs = {
  start_date: "2021-03-07",
};

const mockClaims = {
  continuous: new MockClaimBuilder().continuous(leavePeriodAttrs).create(),
  intermittent: new MockClaimBuilder().intermittent(leavePeriodAttrs).create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "previous-leaves-same-reason",
  mockClaims
);
export default config;
export const Default = DefaultStory;
