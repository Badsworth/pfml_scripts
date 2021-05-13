import { MockBenefitsApplicationBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  empty: new MockBenefitsApplicationBuilder().create(),
  "notified employer": new MockBenefitsApplicationBuilder()
    .notifiedEmployer()
    .create(),
  "didn't notify employer": new MockBenefitsApplicationBuilder()
    .notNotifiedEmployer()
    .create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "notified-employer",
  mockClaims
);
export default config;
export const Default = DefaultStory;
