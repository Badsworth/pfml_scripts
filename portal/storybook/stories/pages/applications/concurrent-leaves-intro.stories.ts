import { MockBenefitsApplicationBuilder } from "lib/mock-helpers/mock-model-builder";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  "continuous leave": new MockBenefitsApplicationBuilder()
    .continuous()
    .create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "concurrent-leaves-intro",
  mockClaims
);

export default config;
export const Default = DefaultStory;
