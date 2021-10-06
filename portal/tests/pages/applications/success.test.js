import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { cleanup, screen } from "@testing-library/react";
import { DateTime } from "luxon";
import Success from "../../../src/pages/applications/success";
import { setupBenefitsApplications } from "../../test-utils/helpers";

const setup = ({ claim }) => {
  return renderPage(
    Success,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic, [claim]);
      },
    },
    { query: { claim_id: "mock_application_id" } }
  );
};

describe("Success", () => {
  const futureDate = DateTime.local().plus({ months: 1 }).toISODate();
  /**
   * Output a snapshot for each of these claim variations
   */
  const variations = {
    "Medical (Not pregnant)": new MockBenefitsApplicationBuilder()
      .continuous({ start_date: "2020-01-01" })
      .medicalLeaveReason()
      .absenceId()
      .create(),
    "Medical (Pregnant)": new MockBenefitsApplicationBuilder()
      .continuous({ start_date: "2020-01-01" })
      .medicalLeaveReason()
      .pregnant()
      .absenceId()
      .create(),
    "Medical (Pregnant, applying in advance)":
      new MockBenefitsApplicationBuilder()
        .continuous({ start_date: futureDate })
        .medicalLeaveReason()
        .pregnant()
        .absenceId()
        .create(),
    "Family (Bonding Newborn)": new MockBenefitsApplicationBuilder()
      .continuous({ start_date: "2020-01-01" })
      .bondingBirthLeaveReason()
      .absenceId()
      .create(),
    "Family (Bonding Future Newborn)": new MockBenefitsApplicationBuilder()
      .completed()
      .bondingBirthLeaveReason(futureDate)
      .hasFutureChild()
      .absenceId()
      .create(),
    "Family (Bonding Adoption)": new MockBenefitsApplicationBuilder()
      .continuous({ start_date: "2020-01-01" })
      .bondingAdoptionLeaveReason()
      .absenceId()
      .create(),
    "Family (Bonding Future Adoption)": new MockBenefitsApplicationBuilder()
      .completed()
      .bondingAdoptionLeaveReason(futureDate)
      .hasFutureChild()
      .absenceId()
      .create(),
    "Caring Leave": new MockBenefitsApplicationBuilder()
      .continuous({ start_date: "2020-01-01" })
      .caringLeaveReason()
      .absenceId()
      .create(),
  };

  Object.keys(variations).forEach((variation) => {
    it(`renders content tailored to ${variation}`, () => {
      const { container } = setup({ claim: variations[variation] });

      expect(container).toMatchSnapshot();
    });
  });

  it(`only renders reportReductionsMessage when there are no other leaves`, () => {
    setup({ claim: variations["Medical (Not pregnant)"] });
    expect(
      screen.getByRole("heading", {
        name: "We may need more information from you",
      })
    ).toBeInTheDocument();

    const claimWithOtherLeave = new MockBenefitsApplicationBuilder()
      .continuous({ start_date: "2020-01-01" })
      .medicalLeaveReason()
      .noOtherLeave() // sets null values to false which make hasReductionsData true
      .absenceId()
      .create();

    cleanup();
    setup({ claim: claimWithOtherLeave });
    expect(
      screen.queryByRole("heading", {
        name: "We may need more information from you",
      })
    ).not.toBeInTheDocument();
  });
});
