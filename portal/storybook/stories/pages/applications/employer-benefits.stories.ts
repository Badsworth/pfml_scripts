import { MockBenefitsApplicationBuilder } from "lib/mock-helpers/mock-model-builder";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  "continuous leave": new MockBenefitsApplicationBuilder()
    .continuous()
    .create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "employer-benefits",
  mockClaims
);

export default config;
export const Default = DefaultStory;
