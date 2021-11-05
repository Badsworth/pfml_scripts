import { MockBenefitsApplicationBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  "continuous leave": new MockBenefitsApplicationBuilder()
    .continuous()
    .create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "concurrent-leaves-intro",
  // @ts-expect-error ts-migrate(2345) FIXME: Argument of type '{ "continuous leave": BenefitsAp... Remove this comment to see the full error message
  mockClaims
);

export default config;
export const Default = DefaultStory;
