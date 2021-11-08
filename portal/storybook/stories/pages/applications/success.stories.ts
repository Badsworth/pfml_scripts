import { DateTime } from "luxon";
import { MockBenefitsApplicationBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const futureDate = DateTime.local().plus({ months: 1 }).toISODate();

const mockClaims = {
  "Medical (Not pregnant)": new MockBenefitsApplicationBuilder()
    .continuous({ start_date: "2020-01-01" })
    .medicalLeaveReason()
    .absenceId()
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'create' does not exist on type 'BaseMock... Remove this comment to see the full error message
    .create(),
  "Medical (Pregnant)": new MockBenefitsApplicationBuilder()
    .continuous({ start_date: "2020-01-01" })
    .medicalLeaveReason()
    .pregnant()
    .absenceId()
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'create' does not exist on type 'BaseMock... Remove this comment to see the full error message
    .create(),
  "Medical (Pregnant, applying in advance)":
    new MockBenefitsApplicationBuilder()
      .continuous({ start_date: futureDate })
      .medicalLeaveReason()
      .pregnant()
      .absenceId()
      // @ts-expect-error ts-migrate(2339) FIXME: Property 'create' does not exist on type 'BaseMock... Remove this comment to see the full error message
      .create(),
  "Family (Bonding Newborn)": new MockBenefitsApplicationBuilder()
    .continuous({ start_date: "2020-01-01" })
    .bondingBirthLeaveReason()
    .absenceId()
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'create' does not exist on type 'BaseMock... Remove this comment to see the full error message
    .create(),
  "Family (Bonding Future Newborn)": new MockBenefitsApplicationBuilder()
    .continuous({ start_date: futureDate })
    .hasFutureChild()
    .bondingBirthLeaveReason(futureDate)
    .absenceId()
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'create' does not exist on type 'BaseMock... Remove this comment to see the full error message
    .create(),
  "Family (Bonding Adoption)": new MockBenefitsApplicationBuilder()
    .continuous({ start_date: "2020-01-01" })
    .bondingAdoptionLeaveReason()
    .absenceId()
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'create' does not exist on type 'BaseMock... Remove this comment to see the full error message
    .create(),
  "Family (Bonding Future Adoption)": new MockBenefitsApplicationBuilder()
    .continuous({ start_date: futureDate })
    .hasFutureChild()
    .bondingAdoptionLeaveReason(futureDate)
    .absenceId()
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'create' does not exist on type 'BaseMock... Remove this comment to see the full error message
    .create(),
  "Caring Leave": new MockBenefitsApplicationBuilder()
    .continuous({ start_date: "2020-01-01" })
    .caringLeaveReason()
    .absenceId()
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'create' does not exist on type 'BaseMock... Remove this comment to see the full error message
    .create(),
};

// @ts-expect-error ts-migrate(2345) FIXME: Argument of type '{ "Medical (Not pregnant)": any;... Remove this comment to see the full error message
const { config, DefaultStory } = generateClaimPageStory("success", mockClaims);
export default config;
export const Default = DefaultStory;
