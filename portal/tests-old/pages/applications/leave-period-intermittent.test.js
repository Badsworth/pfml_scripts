import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import LeavePeriodIntermittent from "../../../src/pages/applications/leave-period-intermittent";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";

jest.mock("../../../src/hooks/useAppLogic");

describe("LeavePeriodIntermittent", () => {
  it("renders the page with bonding leave content", () => {
    const claim = new MockBenefitsApplicationBuilder()
      .bondingBirthLeaveReason()
      .create();

    const { wrapper } = renderWithAppLogic(LeavePeriodIntermittent, {
      claimAttrs: claim,
    });
    const Label = wrapper.find("InputChoiceGroup").prop("label");
    const labelWrapper = shallow(Label);

    expect(wrapper).toMatchSnapshot();
    expect(labelWrapper).toMatchSnapshot();

    wrapper
      .find("Trans")
      .forEach((trans) => expect(trans.dive()).toMatchSnapshot());
  });

  it("renders the page with medical leave content", () => {
    const claim = new MockBenefitsApplicationBuilder()
      .medicalLeaveReason()
      .create();

    const { wrapper } = renderWithAppLogic(LeavePeriodIntermittent, {
      claimAttrs: claim,
    });

    expect(wrapper).toMatchSnapshot();
    wrapper
      .find("Trans")
      .forEach((trans) => expect(trans.dive()).toMatchSnapshot());
  });

  it("displays date fields when user indicates they have this leave period and no other leave period type", () => {
    const claim = new MockBenefitsApplicationBuilder()
      .bondingBirthLeaveReason()
      .create();

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

    changeRadioGroup("has_intermittent_leave_periods", true);

    expect(
      wrapper
        .find("InputDate")
        .first()
        .parents("ConditionalContent")
        .prop("visible")
    ).toBe(true);
  });

  it("adds empty leave period when user first indicates they have this leave period", async () => {
    const { appLogic, claim, wrapper } = renderWithAppLogic(
      LeavePeriodIntermittent,
      {
        claimAttrs: new MockBenefitsApplicationBuilder()
          .medicalLeaveReason()
          .create(),
        render: "mount", // support useEffect
      }
    );
    const { changeRadioGroup, submitForm } = simulateEvents(wrapper);

    // Trigger the effect
    changeRadioGroup("has_intermittent_leave_periods", "true");

    // Submit the form and assert against what's submitted
    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        has_intermittent_leave_periods: true,
        leave_details: {
          intermittent_leave_periods: [{}],
        },
      }
    );
  });

  it("adds empty leave period when user first indicates they have this leave period but also already have a continuous leave period", async () => {
    const { appLogic, claim, wrapper } = renderWithAppLogic(
      LeavePeriodIntermittent,
      {
        claimAttrs: new MockBenefitsApplicationBuilder()
          .medicalLeaveReason()
          .continuous()
          .create(),
        render: "mount", // support useEffect
      }
    );
    const { changeRadioGroup } = simulateEvents(wrapper);

    // Trigger the effect
    changeRadioGroup("has_intermittent_leave_periods", "true");

    // Submit the form and assert against what's submitted
    await act(async () => {
      await wrapper.find("form").simulate("submit");
    });

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        has_intermittent_leave_periods: true,
        leave_details: {
          intermittent_leave_periods: [{}],
        },
      }
    );
  });

  it("displays warning when user indicates they have this leave period and already have another leave period type", () => {
    const claim = new MockBenefitsApplicationBuilder()
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

    changeRadioGroup("has_intermittent_leave_periods", true);

    expect(
      wrapper
        .find("Alert[state='warning']")
        .first()
        .parents("ConditionalContent")
        .prop("visible")
    ).toBe(true);
  });

  it("sends intermittent leave dates and ID to the api when the claim already has data", async () => {
    const claim = new MockBenefitsApplicationBuilder().intermittent().create();
    const { end_date, start_date, leave_period_id } =
      claim.leave_details.intermittent_leave_periods[0];

    const { appLogic, wrapper } = renderWithAppLogic(LeavePeriodIntermittent, {
      claimAttrs: claim,
    });

    const { submitForm } = simulateEvents(wrapper);

    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        has_intermittent_leave_periods: true,
        leave_details: {
          intermittent_leave_periods: [
            { end_date, start_date, leave_period_id },
          ],
        },
      }
    );
  });

  it("sends intermittent leave dates and ID to the api when the user enters new data", async () => {
    const claim = new MockBenefitsApplicationBuilder().create();
    const startDate = "2021-01-01";
    const endDate = "2021-03-01";

    const { appLogic, wrapper } = renderWithAppLogic(LeavePeriodIntermittent, {
      claimAttrs: claim,
    });

    const { changeField, changeRadioGroup, submitForm } =
      simulateEvents(wrapper);

    changeRadioGroup("has_intermittent_leave_periods", true);
    changeField(
      "leave_details.intermittent_leave_periods[0].start_date",
      startDate
    );
    changeField(
      "leave_details.intermittent_leave_periods[0].end_date",
      endDate
    );

    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        has_intermittent_leave_periods: true,
        leave_details: {
          intermittent_leave_periods: [
            { end_date: endDate, start_date: startDate },
          ],
        },
      }
    );
  });
});
