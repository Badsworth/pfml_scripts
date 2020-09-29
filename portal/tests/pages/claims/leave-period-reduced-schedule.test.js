import {
  MockClaimBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import LeavePeriodReducedSchedule from "../../../src/pages/claims/leave-period-reduced-schedule";

jest.mock("../../../src/hooks/useAppLogic");

describe("LeavePeriodReducedSchedule", () => {
  it("renders the page with bonding leave content", () => {
    const claim = new MockClaimBuilder().bondingBirthLeaveReason().create();

    const { wrapper } = renderWithAppLogic(LeavePeriodReducedSchedule, {
      claimAttrs: claim,
    });

    expect(wrapper).toMatchSnapshot();
    wrapper
      .find("Trans")
      .forEach((trans) => expect(trans.dive()).toMatchSnapshot());
  });

  it("renders the page with medical leave content", () => {
    const claim = new MockClaimBuilder().medicalLeaveReason().create();

    const { wrapper } = renderWithAppLogic(LeavePeriodReducedSchedule, {
      claimAttrs: claim,
    });

    expect(wrapper).toMatchSnapshot();
    wrapper
      .find("Trans")
      .forEach((trans) => expect(trans.dive()).toMatchSnapshot());
  });

  it("displays date fields when user indicates they have this leave period", () => {
    const claim = new MockClaimBuilder().bondingBirthLeaveReason().create();

    const { wrapper } = renderWithAppLogic(LeavePeriodReducedSchedule, {
      claimAttrs: claim,
    });
    const { changeRadioGroup } = simulateEvents(wrapper);

    expect(wrapper.find("ConditionalContent").prop("visible")).toBeFalsy();
    changeRadioGroup("temp.has_reduced_schedule_leave_periods", true);
    expect(wrapper.find("ConditionalContent").prop("visible")).toBe(true);
  });

  it("sends reduced schedule leave dates to the api", () => {
    const claim = new MockClaimBuilder().reducedSchedule().create();
    const {
      end_date,
      start_date,
      leave_period_id,
    } = claim.leave_details.reduced_schedule_leave_periods[0];

    const { appLogic, wrapper } = renderWithAppLogic(
      LeavePeriodReducedSchedule,
      {
        claimAttrs: claim,
      }
    );

    wrapper.find("QuestionPage").simulate("save");

    expect(appLogic.claims.update).toHaveBeenCalledWith(claim.application_id, {
      leave_details: {
        reduced_schedule_leave_periods: [
          { end_date, start_date, leave_period_id },
        ],
      },
      temp: {
        has_reduced_schedule_leave_periods: true,
      },
    });
  });
});
