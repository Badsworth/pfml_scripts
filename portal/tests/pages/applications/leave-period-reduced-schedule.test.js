import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import LeavePeriodReducedSchedule from "../../../src/pages/applications/leave-period-reduced-schedule";

jest.mock("../../../src/hooks/useAppLogic");

describe("LeavePeriodReducedSchedule", () => {
  it("renders the page with bonding leave content", () => {
    const claim = new MockBenefitsApplicationBuilder()
      .bondingBirthLeaveReason()
      .create();

    const { wrapper } = renderWithAppLogic(LeavePeriodReducedSchedule, {
      claimAttrs: claim,
    });

    expect(wrapper).toMatchSnapshot();
    wrapper
      .find("Trans")
      .forEach((trans) => expect(trans.dive()).toMatchSnapshot());
  });

  it("renders the page with medical leave content", () => {
    const claim = new MockBenefitsApplicationBuilder()
      .medicalLeaveReason()
      .create();

    const { wrapper } = renderWithAppLogic(LeavePeriodReducedSchedule, {
      claimAttrs: claim,
    });

    expect(wrapper).toMatchSnapshot();
    wrapper
      .find("Trans")
      .forEach((trans) => expect(trans.dive()).toMatchSnapshot());
  });

  it("displays date fields when user indicates they have this leave period", () => {
    const claim = new MockBenefitsApplicationBuilder()
      .bondingBirthLeaveReason()
      .create();

    const { wrapper } = renderWithAppLogic(LeavePeriodReducedSchedule, {
      claimAttrs: claim,
    });
    const { changeRadioGroup } = simulateEvents(wrapper);

    expect(wrapper.find("ConditionalContent").prop("visible")).toBeFalsy();
    changeRadioGroup("has_reduced_schedule_leave_periods", true);
    expect(wrapper.find("ConditionalContent").prop("visible")).toBe(true);
  });

  it("adds empty leave period when user first indicates they have this leave period", async () => {
    const { appLogic, claim, wrapper } = renderWithAppLogic(
      LeavePeriodReducedSchedule,
      {
        claimAttrs: new MockBenefitsApplicationBuilder()
          .medicalLeaveReason()
          .create(),
        render: "mount", // support useEffect
      }
    );
    const { changeRadioGroup, submitForm } = simulateEvents(wrapper);

    // Trigger the effect
    changeRadioGroup("has_reduced_schedule_leave_periods", "true");

    // Submit the form and assert against what's submitted
    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        has_reduced_schedule_leave_periods: true,
        leave_details: {
          reduced_schedule_leave_periods: [{}],
        },
      }
    );
  });

  it("sends reduced schedule leave dates and ID to the api when the claim already has data", async () => {
    const claim = new MockBenefitsApplicationBuilder()
      .reducedSchedule()
      .create();
    const { end_date, start_date, leave_period_id } =
      claim.leave_details.reduced_schedule_leave_periods[0];

    const { appLogic, wrapper } = renderWithAppLogic(
      LeavePeriodReducedSchedule,
      {
        claimAttrs: claim,
      }
    );

    const { submitForm } = simulateEvents(wrapper);

    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        has_reduced_schedule_leave_periods: true,
        leave_details: {
          reduced_schedule_leave_periods: [
            { end_date, start_date, leave_period_id },
          ],
        },
      }
    );
  });

  it("sends reduced schedule leave dates and ID to the api when the claim has newly entered data", async () => {
    const claim = new MockBenefitsApplicationBuilder().create();
    const start_date = "2021-01-01";
    const end_date = "2021-03-01";

    const { appLogic, wrapper } = renderWithAppLogic(
      LeavePeriodReducedSchedule,
      {
        claimAttrs: claim,
      }
    );

    const { changeField, changeRadioGroup, submitForm } =
      simulateEvents(wrapper);

    changeRadioGroup("has_reduced_schedule_leave_periods", "true");
    changeField(
      "leave_details.reduced_schedule_leave_periods[0].start_date",
      start_date
    );
    changeField(
      "leave_details.reduced_schedule_leave_periods[0].end_date",
      end_date
    );

    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        has_reduced_schedule_leave_periods: true,
        leave_details: {
          reduced_schedule_leave_periods: [{ end_date, start_date }],
        },
      }
    );
  });
});
