import { MockBenefitsApplicationBuilder } from "tests/test-utils";
import { WorkPatternType } from "src/models/BenefitsApplication";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  fixed: new MockBenefitsApplicationBuilder()
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
