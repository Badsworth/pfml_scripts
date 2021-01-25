import { MockClaimBuilder } from "tests/test-utils";
import { WorkPatternType } from "src/models/Claim";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  fixed: new MockClaimBuilder()
    .continuous()
    .workPattern({ work_pattern_type: WorkPatternType.variable })
    .create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "schedule-variable",
  mockClaims
);
export default config;
export const Default = DefaultStory;
