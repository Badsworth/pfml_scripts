import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
} from "../../test-utils";
import { DateTime } from "luxon";
import Success from "../../../src/pages/applications/success";

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
      const claim = variations[variation];
      const { wrapper } = renderWithAppLogic(Success, {
        claimAttrs: claim,
      });

      expect(wrapper).toMatchSnapshot();

      const transElements = wrapper.find("Trans");
      transElements.forEach((el) => expect(el.dive()).toMatchSnapshot());
    });
  });

  it(`renders reportReductionsMessage when there are no other leaves`, () => {
    const claim = new MockBenefitsApplicationBuilder()
      .continuous({ start_date: "2020-01-01" })
      .medicalLeaveReason()
      .absenceId()
      .create();

    const { wrapper } = renderWithAppLogic(Success, {
      claimAttrs: claim,
    });

    expect(
      wrapper
        .find(`Trans[i18nKey="pages.claimsSuccess.reportReductionsMessage"]`)
        .dive()
    ).toMatchSnapshot();

    expect(
      wrapper
        .find(`Trans[i18nKey="pages.claimsSuccess.reportReductionsProcess"]`)
        .exists()
    ).toEqual(false);
  });

  it(`does not render reportReductionsMessage when there are other leaves`, () => {
    const claim = new MockBenefitsApplicationBuilder()
      .continuous({ start_date: "2020-01-01" })
      .medicalLeaveReason()
      .noOtherLeave() // sets null values to false which make hasReductionsData true
      .absenceId()
      .create();

    const { wrapper } = renderWithAppLogic(Success, {
      claimAttrs: claim,
    });

    expect(
      wrapper
        .find(`Trans[i18nKey="pages.claimsSuccess.reportReductionsMessage"]`)
        .exists()
    ).toEqual(false);

    expect(
      wrapper
        .find(`Trans[i18nKey="pages.claimsSuccess.reportReductionsProcess"]`)
        .exists()
    ).toEqual(false);
  });
});
