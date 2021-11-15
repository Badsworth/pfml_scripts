import { MockBenefitsApplicationBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  "state id": new MockBenefitsApplicationBuilder().hasStateId().create(),
  "other id": new MockBenefitsApplicationBuilder().hasOtherId().create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "upload-id",
  mockClaims
);
export default config;
export const Default = DefaultStory;
