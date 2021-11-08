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
  // @ts-expect-error ts-migrate(2345) FIXME: Argument of type '{ fixed: BenefitsApplication; }'... Remove this comment to see the full error message
  mockClaims
);
export default config;
export const Default = DefaultStory;
