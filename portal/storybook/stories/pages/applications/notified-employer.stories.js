import { MockClaimBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  empty: new MockClaimBuilder().create(),
  "notified employer": new MockClaimBuilder().notifiedEmployer().create(),
  "didn't notify employer": new MockClaimBuilder()
    .notNotifiedEmployer()
    .create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "notified-employer",
  mockClaims
);
export default config;
export const Default = DefaultStory;
