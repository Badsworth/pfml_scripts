import { DateTime } from "luxon";
import { MockClaimBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const futureDate = DateTime.local().plus({ months: 1 }).toISODate();

const mockClaims = {
  "Medical (Not pregnant)": new MockClaimBuilder()
    .continuous({ start_date: "2020-01-01" })
    .medicalLeaveReason()
    .absenceId()
    .create(),
  "Medical (Pregnant)": new MockClaimBuilder()
    .continuous({ start_date: "2020-01-01" })
    .medicalLeaveReason()
    .pregnant()
    .absenceId()
    .create(),
  "Medical (Pregnant, applying in advance)": new MockClaimBuilder()
    .continuous({ start_date: futureDate })
    .medicalLeaveReason()
    .pregnant()
    .absenceId()
    .create(),
  "Family (Bonding Newborn)": new MockClaimBuilder()
    .continuous({ start_date: "2020-01-01" })
    .bondingBirthLeaveReason()
    .absenceId()
    .create(),
  "Family (Bonding Future Newborn)": new MockClaimBuilder()
    .continuous({ start_date: futureDate })
    .bondingBirthLeaveReason(futureDate)
    .absenceId()
    .create(),
  "Family (Bonding Adoption)": new MockClaimBuilder()
    .continuous({ start_date: "2020-01-01" })
    .bondingAdoptionLeaveReason()
    .absenceId()
    .create(),
  "Family (Bonding Future Adoption)": new MockClaimBuilder()
    .continuous({ start_date: futureDate })
    .bondingAdoptionLeaveReason(futureDate)
    .absenceId()
    .create(),
};

const { config, DefaultStory } = generateClaimPageStory("success", mockClaims);
export default config;
export const Default = DefaultStory;
