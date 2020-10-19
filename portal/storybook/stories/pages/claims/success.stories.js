import { DateTime } from "luxon";
import { MockClaimBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  "Medical (Not pregnant)": new MockClaimBuilder()
    .completed()
    .medicalLeaveReason()
    .create(),
  "Medical (Pregnant)": new MockClaimBuilder()
    .completed()
    .medicalLeaveReason()
    .pregnant()
    .create(),
  "Family (Bonding Newborn)": new MockClaimBuilder()
    .completed()
    .bondingBirthLeaveReason()
    .create(),
  "Family (Bonding Future Newborn)": new MockClaimBuilder()
    .completed()
    .bondingBirthLeaveReason(DateTime.local().plus({ months: 1 }).toISODate())
    .create(),
  "Family (Bonding Adoption)": new MockClaimBuilder()
    .completed()
    .bondingAdoptionLeaveReason()
    .create(),
  "Family (Bonding Future Adoption)": new MockClaimBuilder()
    .completed()
    .bondingAdoptionLeaveReason(
      DateTime.local().plus({ months: 1 }).toISODate()
    )
    .create(),
};

const { config, DefaultStory } = generateClaimPageStory("success", mockClaims);
export default config;
export const Default = DefaultStory;
