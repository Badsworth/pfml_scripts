import { MockClaimBuilder, renderWithAppLogic } from "../../test-utils";
import { DateTime } from "luxon";
import Success from "../../../src/pages/claims/success";

describe("Success", () => {
  /**
   * Output a snapshot for each of these claim variations
   */
  const variations = {
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

  Object.keys(variations).forEach((variation) => {
    it(`renders content tailored to ${variation}`, () => {
      const claim = variations[variation];
      const { wrapper } = renderWithAppLogic(Success, {
        claimAttrs: claim,
      });

      expect(wrapper).toMatchSnapshot();
    });
  });
});
