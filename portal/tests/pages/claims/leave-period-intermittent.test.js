import {
  MockClaimBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import LeavePeriodIntermittent from "../../../src/pages/claims/leave-period-intermittent";

jest.mock("../../../src/hooks/useAppLogic");

describe("LeavePeriodIntermittent", () => {
  it("renders the page with bonding leave content", () => {
    const claim = new MockClaimBuilder().bondingBirthLeaveReason().create();

    const { wrapper } = renderWithAppLogic(LeavePeriodIntermittent, {
      claimAttrs: claim,
    });

    expect(wrapper).toMatchSnapshot();
    wrapper
      .find("Trans")
      .forEach((trans) => expect(trans.dive()).toMatchSnapshot());
  });

  it("renders the page with medical leave content", () => {
    const claim = new MockClaimBuilder().medicalLeaveReason().create();

    const { wrapper } = renderWithAppLogic(LeavePeriodIntermittent, {
      claimAttrs: claim,
    });

    expect(wrapper).toMatchSnapshot();
    wrapper
      .find("Trans")
      .forEach((trans) => expect(trans.dive()).toMatchSnapshot());
  });

  it("displays date fields when user indicates they have this leave period and no other leave period type", () => {
    const claim = new MockClaimBuilder().bondingBirthLeaveReason().create();

    const { wrapper } = renderWithAppLogic(LeavePeriodIntermittent, {
      claimAttrs: claim,
    });
    const { changeRadioGroup } = simulateEvents(wrapper);

    expect(
      wrapper
        .find("InputDate")
        .first()
        .parents("ConditionalContent")
        .prop("visible")
    ).toBeFalsy();

    changeRadioGroup("temp.has_intermittent_leave_periods", true);

    expect(
      wrapper
        .find("InputDate")
        .first()
        .parents("ConditionalContent")
        .prop("visible")
    ).toBe(true);
  });

  it("displays warning when user indicates they have this leave period and already have another leave period type", () => {
    const claim = new MockClaimBuilder()
      .bondingBirthLeaveReason()
      .continuous()
      .create();

    const { wrapper } = renderWithAppLogic(LeavePeriodIntermittent, {
      claimAttrs: claim,
    });
    const { changeRadioGroup } = simulateEvents(wrapper);

    expect(
      wrapper
        .find("Alert[state='warning']")
        .first()
        .parents("ConditionalContent")
        .prop("visible")
    ).toBeFalsy();

    changeRadioGroup("temp.has_intermittent_leave_periods", true);

    expect(
      wrapper
        .find("Alert[state='warning']")
        .first()
        .parents("ConditionalContent")
        .prop("visible")
    ).toBe(true);
  });

  it("sends intermittent leave dates to the api", () => {
    const claim = new MockClaimBuilder().intermittent().create();
    const {
      end_date,
      start_date,
      leave_period_id,
    } = claim.leave_details.intermittent_leave_periods[0];

    const { appLogic, wrapper } = renderWithAppLogic(LeavePeriodIntermittent, {
      claimAttrs: claim,
    });

    wrapper.find("QuestionPage").simulate("save");

    expect(appLogic.claims.update).toHaveBeenCalledWith(claim.application_id, {
      leave_details: {
        intermittent_leave_periods: [{ end_date, start_date, leave_period_id }],
      },
      temp: {
        has_intermittent_leave_periods: true,
      },
    });
  });
});
