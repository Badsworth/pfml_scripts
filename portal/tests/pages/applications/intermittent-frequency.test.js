import {
  DurationBasis,
  FrequencyIntervalBasis,
  IntermittentLeavePeriod,
} from "../../../src/models/Claim";
import IntermittentFrequency, {
  irregularOver6MonthsId,
} from "../../../src/pages/applications/intermittent-frequency";
import { MockClaimBuilder, renderWithAppLogic } from "../../test-utils";
import { act } from "react-dom/test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("IntermittentFrequency", () => {
  const intermittentClaimAttrs = (attrs) => ({
    leave_details: {
      intermittent_leave_periods: [new IntermittentLeavePeriod({ ...attrs })],
    },
  });

  it("renders the page", () => {
    const { wrapper } = renderWithAppLogic(IntermittentFrequency);

    expect(wrapper).toMatchSnapshot();
  });

  it("it displays frequency and duration_basis questions when a frequency_interval_basis is selected", () => {
    const { wrapper: blankClaimWrapper } = renderWithAppLogic(
      IntermittentFrequency
    );
    const { wrapper: wrapperWithState } = renderWithAppLogic(
      IntermittentFrequency,
      {
        claimAttrs: intermittentClaimAttrs({
          frequency_interval_basis: FrequencyIntervalBasis.months,
        }),
      }
    );

    expect(
      blankClaimWrapper.find("ConditionalContent").at(0).prop("visible")
    ).toBe(false);
    expect(
      wrapperWithState.find("ConditionalContent").at(0).prop("visible")
    ).toBe(true);
  });

  it("it displays duration question when a duration_basis is selected", () => {
    const { wrapper: blankClaimWrapper } = renderWithAppLogic(
      IntermittentFrequency
    );
    const { wrapper: wrapperWithState } = renderWithAppLogic(
      IntermittentFrequency,
      {
        claimAttrs: intermittentClaimAttrs({
          duration_basis: DurationBasis.days,
        }),
      }
    );

    expect(
      blankClaimWrapper.find("ConditionalContent").at(1).prop("visible")
    ).toBe(false);
    expect(
      wrapperWithState.find("ConditionalContent").at(1).prop("visible")
    ).toBe(true);
  });

  it("displays frequency label corresponding to selected frequency interval and basis", () => {
    expect.assertions();

    const options = [
      {
        frequency_interval_basis: FrequencyIntervalBasis.weeks,
      },
      {
        frequency_interval_basis: FrequencyIntervalBasis.months,
      },
      {
        frequency_interval: 6,
        frequency_interval_basis: FrequencyIntervalBasis.months,
      },
    ];

    options.forEach((option) => {
      const { wrapper } = renderWithAppLogic(IntermittentFrequency, {
        claimAttrs: intermittentClaimAttrs(option),
      });

      expect(
        wrapper
          .find({
            name: "leave_details.intermittent_leave_periods[0].frequency",
          })
          .prop("label")
      ).toMatchSnapshot();
    });
  });

  it("displays duration label corresponding to selected duration basis", () => {
    expect.assertions();

    const options = [
      {
        duration_basis: DurationBasis.days,
      },
      {
        duration_basis: DurationBasis.hours,
      },
    ];

    options.forEach((option) => {
      const { wrapper } = renderWithAppLogic(IntermittentFrequency, {
        claimAttrs: intermittentClaimAttrs(option),
      });

      expect(
        wrapper
          .find({
            name: "leave_details.intermittent_leave_periods[0].duration",
          })
          .prop("label")
      ).toMatchSnapshot();
    });
  });

  it("displays Alert about having medical form when claim is for Medical leave", () => {
    const { wrapper: medicalWrapper } = renderWithAppLogic(
      IntermittentFrequency,
      {
        claimAttrs: new MockClaimBuilder().medicalLeaveReason().create(),
      }
    );
    const { wrapper: bondingWrapper } = renderWithAppLogic(
      IntermittentFrequency,
      {
        claimAttrs: new MockClaimBuilder().bondingBirthLeaveReason().create(),
      }
    );
    const alert = medicalWrapper.find("Alert");

    expect(alert.exists()).toBe(true);
    expect(alert).toMatchSnapshot();
    expect(bondingWrapper.find("Alert").exists()).toBe(false);
  });

  it("displays hint text with medical form context when claim is for Medical leave", () => {
    expect.assertions();

    const { wrapper: medicalWrapper } = renderWithAppLogic(
      IntermittentFrequency,
      {
        claimAttrs: new MockClaimBuilder().medicalLeaveReason().create(),
      }
    );
    const { wrapper: bondingWrapper } = renderWithAppLogic(
      IntermittentFrequency,
      {
        claimAttrs: new MockClaimBuilder().bondingBirthLeaveReason().create(),
      }
    );

    const fieldFinder = (nodeWrapper) =>
      ["InputText", "InputChoiceGroup"].includes(nodeWrapper.name());
    const medicalWrapperFields = medicalWrapper.findWhere(fieldFinder);
    const bondingWrapperFields = bondingWrapper.findWhere(fieldFinder);

    medicalWrapperFields.forEach((field) => {
      expect(field.prop("hint")).toMatchSnapshot();
    });

    bondingWrapperFields.forEach((field) => {
      expect(field.prop("hint")).toBeNull();
    });
  });

  describe("frequency_basis change handler", () => {
    let wrapper;
    const claimAttrs = intermittentClaimAttrs();
    const frequencyBasisInputName =
      "leave_details.intermittent_leave_periods[0].frequency_interval_basis";

    beforeEach(() => {
      ({ wrapper } = renderWithAppLogic(IntermittentFrequency, {
        claimAttrs,
      }));
    });

    it("selects Months radio", () => {
      act(() => {
        wrapper.find({ name: frequencyBasisInputName }).simulate("change", {
          preventDefault: jest.fn(),
          target: {
            name: frequencyBasisInputName,
            value: FrequencyIntervalBasis.months,
          },
        });
      });

      const choices = wrapper
        .find({ name: frequencyBasisInputName })
        .prop("choices");

      expect(choices[1].checked).toBe(true);
    });

    it("selects 'Irregular over 6 months' radio when input ID matches", () => {
      act(() => {
        wrapper.find({ name: frequencyBasisInputName }).simulate("change", {
          preventDefault: jest.fn(),
          target: {
            id: irregularOver6MonthsId,
            name: frequencyBasisInputName,
            value: FrequencyIntervalBasis.months,
          },
        });
      });

      const choices = wrapper
        .find({ name: frequencyBasisInputName })
        .prop("choices");

      expect(choices[2].checked).toBe(true);
    });
  });

  it("sends the page's fields and the leave period ID to the API", () => {
    const claim = new MockClaimBuilder().intermittent().create();
    const {
      duration,
      duration_basis,
      frequency,
      frequency_interval,
      frequency_interval_basis,
      leave_period_id,
    } = claim.leave_details.intermittent_leave_periods[0];

    const { appLogic, wrapper } = renderWithAppLogic(IntermittentFrequency, {
      claimAttrs: claim,
    });

    wrapper.find("QuestionPage").simulate("save");

    expect(appLogic.claims.update).toHaveBeenCalledWith(claim.application_id, {
      leave_details: {
        intermittent_leave_periods: [
          {
            duration,
            duration_basis,
            frequency,
            frequency_interval,
            frequency_interval_basis,
            leave_period_id,
          },
        ],
      },
    });
  });
});
