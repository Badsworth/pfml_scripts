import { MockClaimBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  medical: new MockClaimBuilder().continuous().medicalLeaveReason().create(),
  bonding: new MockClaimBuilder()
    .continuous()
    .bondingBirthLeaveReason()
    .create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "leave-dates",
  mockClaims
);
export default config;
export const Default = DefaultStory;
