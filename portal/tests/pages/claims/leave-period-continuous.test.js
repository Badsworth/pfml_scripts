import {
  MockClaimBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import LeavePeriodContinuous from "../../../src/pages/claims/leave-period-continuous";

jest.mock("../../../src/hooks/useAppLogic");

describe("LeavePeriodContinuous", () => {
  it("renders the page with bonding leave content", () => {
    const claim = new MockClaimBuilder().bondingBirthLeaveReason().create();

    const { wrapper } = renderWithAppLogic(LeavePeriodContinuous, {
      claimAttrs: claim,
    });

    expect(wrapper).toMatchSnapshot();
    wrapper
      .find("Trans")
      .forEach((trans) => expect(trans.dive()).toMatchSnapshot());
  });

  it("renders the page with medical leave content", () => {
    const claim = new MockClaimBuilder().medicalLeaveReason().create();

    const { wrapper } = renderWithAppLogic(LeavePeriodContinuous, {
      claimAttrs: claim,
    });

    expect(wrapper).toMatchSnapshot();
    wrapper
      .find("Trans")
      .forEach((trans) => expect(trans.dive()).toMatchSnapshot());
  });

  it("displays date fields when user indicates they have this leave period", () => {
    const claim = new MockClaimBuilder().bondingBirthLeaveReason().create();

    const { wrapper } = renderWithAppLogic(LeavePeriodContinuous, {
      claimAttrs: claim,
    });
    const { changeRadioGroup } = simulateEvents(wrapper);

    expect(wrapper.find("ConditionalContent").prop("visible")).toBeFalsy();
    changeRadioGroup("has_continuous_leave_periods", true);
    expect(wrapper.find("ConditionalContent").prop("visible")).toBe(true);
  });

  it("sends continuous leave dates to the api", () => {
    const claim = new MockClaimBuilder().continuous().create();
    const {
      end_date,
      start_date,
      leave_period_id,
    } = claim.leave_details.continuous_leave_periods[0];

    const { appLogic, wrapper } = renderWithAppLogic(LeavePeriodContinuous, {
      claimAttrs: claim,
    });

    wrapper.find("QuestionPage").simulate("save");

    expect(appLogic.claims.update).toHaveBeenCalledWith(claim.application_id, {
      has_continuous_leave_periods: true,
      leave_details: {
        continuous_leave_periods: [{ end_date, start_date, leave_period_id }],
      },
    });
  });
});
