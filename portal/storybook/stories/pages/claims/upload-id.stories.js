import { MockClaimBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  "state id": new MockClaimBuilder().hasStateId().create(),
  "other id": new MockClaimBuilder().hasOtherId().create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "upload-id",
  mockClaims
);
export default config;
export const Default = DefaultStory;
