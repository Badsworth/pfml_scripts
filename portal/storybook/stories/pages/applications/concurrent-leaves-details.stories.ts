import { MockBenefitsApplicationBuilder } from "lib/mock-helpers/mock-model-builder";
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
