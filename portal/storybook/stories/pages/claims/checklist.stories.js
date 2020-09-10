import { MockClaimBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  empty: new MockClaimBuilder().create(),
  "verified id": new MockClaimBuilder().verifiedId().create(),
  "medical leave": new MockClaimBuilder()
    .verifiedId()
    .medicalLeaveReason()
    .create(),
  submitted: new MockClaimBuilder().submitted().create(),
  complete: new MockClaimBuilder().complete().create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "checklist",
  mockClaims
);
export default config;
export const Default = DefaultStory;
