import { DateTime } from "luxon";
import { MockClaimBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const futureDate = DateTime.local().plus({ months: 1 }).toISODate();

const mockClaims = {
  "Medical (Not pregnant)": new MockClaimBuilder()
    .completed()
    .medicalLeaveReason()
    .create(),
  "Medical (Pregnant)": new MockClaimBuilder()
    .continuous({ start_date: "2020-01-01" })
    .medicalLeaveReason()
    .pregnant()
    .create(),
  "Medical (Pregnant, applying in advance)": new MockClaimBuilder()
    .continuous({ start_date: futureDate })
    .medicalLeaveReason()
    .pregnant()
    .create(),
  "Family (Bonding Newborn)": new MockClaimBuilder()
    .completed()
    .bondingBirthLeaveReason()
    .create(),
  "Family (Bonding Future Newborn)": new MockClaimBuilder()
    .completed()
    .bondingBirthLeaveReason(futureDate)
    .create(),
  "Family (Bonding Adoption)": new MockClaimBuilder()
    .completed()
    .bondingAdoptionLeaveReason()
    .create(),
  "Family (Bonding Future Adoption)": new MockClaimBuilder()
    .completed()
    .bondingAdoptionLeaveReason(futureDate)
    .create(),
};

const { config, DefaultStory } = generateClaimPageStory("success", mockClaims);
export default config;
export const Default = DefaultStory;
