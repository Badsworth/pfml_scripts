import { MockClaimBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  bonding: new MockClaimBuilder().bondingBirthLeaveReason().create(),
  caring: new MockClaimBuilder().caringLeaveReason().create(),
  medical: new MockClaimBuilder().medicalLeaveReason().create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "leave-period-continuous",
  mockClaims
);
export default config;
export const Default = DefaultStory;
