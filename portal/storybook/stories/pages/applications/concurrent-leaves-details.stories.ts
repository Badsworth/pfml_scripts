import { MockBenefitsApplicationBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  employed: new MockBenefitsApplicationBuilder().employed().create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "concurrent-leaves-details",
  mockClaims
);
export default config;
export const Default = DefaultStory;
