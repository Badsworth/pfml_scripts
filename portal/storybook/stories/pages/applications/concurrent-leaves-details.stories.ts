import { MockBenefitsApplicationBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  employed: new MockBenefitsApplicationBuilder().employed().create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "concurrent-leaves-details",
  // @ts-expect-error ts-migrate(2345) FIXME: Argument of type '{ employed: BenefitsApplication;... Remove this comment to see the full error message
  mockClaims
);
export default config;
export const Default = DefaultStory;
