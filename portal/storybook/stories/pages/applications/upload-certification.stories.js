import { MockClaimBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  "Medical leave": new MockClaimBuilder().medicalLeaveReason().create(),
  "Bonding: newborn": new MockClaimBuilder().bondingBirthLeaveReason().create(),
  "Bonding: adoption/foster": new MockClaimBuilder()
    .bondingAdoptionLeaveReason()
    .create(),
  Caregiver: new MockClaimBuilder().caringLeaveReason().create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "upload-certification",
  mockClaims
);
export default config;
export const Default = DefaultStory;
