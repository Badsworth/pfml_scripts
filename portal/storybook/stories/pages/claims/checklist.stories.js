import { MockClaimBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  empty: new MockClaimBuilder().create(),
  "verified id": new MockClaimBuilder().verifiedId().create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "checklist",
  mockClaims
);
export default config;
export const Default = DefaultStory;
